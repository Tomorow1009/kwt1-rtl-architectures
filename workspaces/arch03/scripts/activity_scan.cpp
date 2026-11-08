// Streaming VCD structural/activity audit. No power estimation or sampling.
// The Python wrapper checks time boundaries and hashes every byte separately.
#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
using namespace std;
struct Signal { uint64_t width; unsigned roles; };
static void need(bool ok,const char* reason) { if(!ok)throw runtime_error(reason); }
static string trim(const string& s) {
    for(unsigned char c:s)need(c<128,"Non-ASCII VCD record requires review");
    const auto b=s.find_first_not_of(" \t\r\n");
    return b==string::npos?string():s.substr(b,s.find_last_not_of(" \t\r\n")-b+1);
}
static vector<string> words(const string& s) { istringstream in(s);vector<string> v;string w;while(in>>w)v.push_back(w);return v; }
static uint64_t integer(const string& s) {
    need(!s.empty(),"Missing unsigned integer");uint64_t n=0;
    for(char c:s){need(c>='0'&&c<='9',"Invalid unsigned integer");need(n<=(numeric_limits<uint64_t>::max()-(c-'0'))/10,"Integer overflow");n=n*10+c-'0';}return n;
}
int main(int argc,char** argv) {
 try {
    need(argc==2,"Usage: activity_scan file.vcd");ifstream in(argv[1],ios::binary);need(bool(in),"Cannot open VCD");
    const array<string,6> names={{"cpu","itcm","dtcm","accelerator","shared","interconnect"}};
    const array<string,6> hierarchy={{"u_e203_cpu_top","u_e203_itcm_ram","u_e203_dtcm_ram","u_arch03_accel","u_arch03_shared","u_e203_subsys_mems"}};
    vector<string> scope;unordered_map<string,Signal> ids;array<uint64_t,6> roles={{}},events={{}};
    uint64_t tick=0,begin=0,end=0,scale_fs=0,decl=0,changes=0,unknown=0,last=0,intervals=0;
    bool header=true,active=false;string command,line;
    while(getline(in,line)) {
      line=trim(line);if(line.empty())continue;
      if(header) {
        string record=line;
        while(record.find("$end")==string::npos) { need(bool(getline(in,line)),"Incomplete VCD header");record+=' '+trim(line); }
        auto t=words(record);need(!t.empty(),"Empty header record");const string& c=t[0];
        if(c=="$timescale") {
          need(!scale_fs,"Duplicate VCD timescale");string value;size_t i=1;for(;i<t.size()&&t[i]!="$end";++i)value+=t[i];need(i<t.size(),"Missing timescale end");
          size_t p=value.find_first_not_of("0123456789");need(p!=string::npos,"Invalid timescale");auto factor=integer(value.substr(0,p));need(factor==1||factor==10||factor==100,"Unsupported timescale factor");
          const unordered_map<string,uint64_t> units={{"s",1000000000000000ULL},{"ms",1000000000000ULL},{"us",1000000000ULL},{"ns",1000000ULL},{"ps",1000ULL},{"fs",1ULL}};
          auto u=units.find(value.substr(p));need(u!=units.end(),"Unsupported timescale unit");scale_fs=factor*u->second;
        } else if(c=="$scope") { need(t.size()==4,"Malformed scope");scope.push_back(t[2]); }
        else if(c=="$upscope") { need(!scope.empty(),"Unbalanced scope");scope.pop_back(); }
        else if(c=="$var") {
          need(t.size()>=6,"Malformed variable");auto width=integer(t[2]);need(width>0,"Zero width");
          need(scope.size()>=2&&scope[0]=="tb_top"&&scope[1]=="u_e203_soc_top","Signal outside selected SoC");
          unsigned mask=0;for(unsigned k=0;k<6;++k)if(find(scope.begin(),scope.end(),hierarchy[k])!=scope.end()){mask|=1U<<k;++roles[k];}
          auto found=ids.find(t[3]);if(found!=ids.end()){need(found->second.width==width,"Alias width mismatch");found->second.roles|=mask;}else ids.emplace(t[3],Signal{width,mask});++decl;
        } else if(c=="$enddefinitions") {
          need(scope.empty()&&scale_fs&&decl,"Incomplete VCD hierarchy/timescale");for(auto n:roles)need(n>0,"Missing component hierarchy");header=false;
        } else need(c=="$date"||c=="$version"||c=="$comment","Unreviewed header command");
        continue;
      }
      if(line[0]=='#') { need(command.empty(),"Time inside incomplete dump command");auto n=integer(line.substr(1));need(n>=tick,"Time moved backwards");tick=n;continue; }
      if(line[0]=='$') {
        auto t=words(line);const string& c=t[0];
        if(c=="$end") { need(!command.empty()&&t.size()==1,"Orphan dump end");command.clear();continue; }
        if(c=="$comment") {while(line.find("$end")==string::npos)need(bool(getline(in,line)),"Incomplete comment");continue;}
        need(command.empty()&&(c=="$dumpon"||c=="$dumpoff"||c=="$dumpvars"||c=="$dumpall"),"Unreviewed/nested body command");
        need(t.size()==1||(t.size()==2&&t[1]=="$end"),"Inline dump values unsupported");
        if(c=="$dumpon") {need(!active,"Duplicate active dumpon");active=true;begin=tick;}
        else if(c=="$dumpoff") {if(active){need(tick>begin,"Empty dump interval");end=tick;++intervals;active=false;}else need(tick==0,"Unexpected dumpoff");}
        command=t.size()==1?c:string();continue;
      }
      string value,code;char kind=line[0];
      if(string("01xXzZ").find(kind)!=string::npos) {value=line.substr(0,1);code=trim(line.substr(1));}
      else if(string("bBrR").find(kind)!=string::npos) {auto p=line.find_first_of(" \t",1);need(p!=string::npos,"Malformed vector/real");value=line.substr(1,p-1);code=trim(line.substr(p));need(code.find_first_of(" \t")==string::npos,"Malformed identifier");}
      else throw runtime_error("Unreviewed value encoding");
      auto s=ids.find(code);need(s!=ids.end(),"Value for undeclared signal");
      if(kind=='b'||kind=='B'){need(!value.empty()&&value.size()<=s->second.width,"Invalid vector width");need(value.find_first_not_of("01xXzZ")==string::npos,"Invalid vector digits");}
      if(active) {
        ++changes;last=tick;bool bad=value.find_first_of("xXzZ")!=string::npos;
        if(kind=='r'||kind=='R') {char* after=nullptr;double v=strtod(value.c_str(),&after);need(after!=value.c_str()&&after==value.c_str()+value.size(),"Invalid real");bad=bad||!isfinite(v);}
        if(bad)++unknown;for(unsigned k=0;k<6;++k)if(s->second.roles&(1U<<k))++events[k];
      }
    }
    need(in.eof(),"VCD input read error");need(!header&&!active&&command.empty()&&intervals==1,"Require one complete task interval");
    need(changes&&last>begin,"No active task transitions");for(auto n:events)need(n>0,"Missing component activity");
    cout<<"{\"scale_fs\":"<<scale_fs<<",\"begin_tick\":"<<begin<<",\"end_tick\":"<<end
        <<",\"signal_declarations\":"<<decl<<",\"unique_identifiers\":"<<ids.size()
        <<",\"active_value_records\":"<<changes<<",\"unknown_value_records\":"<<unknown;
    for(unsigned mode=0;mode<2;++mode){cout<<",\""<<(mode?"component_value_records":"component_declarations")<<"\":{";for(unsigned k=0;k<6;++k){if(k)cout<<",";cout<<'"'<<names[k]<<"\":"<<(mode?events[k]:roles[k]);}cout<<"}";}
    cout<<"}\n";return 0;
 } catch(const exception& e) {cerr<<"ACTIVITY_AUDIT_ERROR "<<e.what()<<"\n";return 1;}
}
