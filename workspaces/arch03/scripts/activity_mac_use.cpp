// Independent full-stream unknown localization plus MAC acceptance sampling.
// Derived from activity_unknown.cpp, which remains frozen and unchanged.
// Sample PRE-timestamp values at each observed rising edge, never post-NBA data.
#include <algorithm>
#include <array>
#include <cmath>
#include <cctype>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <limits>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
using namespace std;
struct Signal {
    uint64_t width=0, records=0, unknown=0, initial_unknown=0, later_unknown=0;
    uint64_t first=0, last=0, first_unknown=0, last_unknown=0, unknown_ticks=0;
    unsigned roles=0;
    bool seen=false, bad=false;
    vector<string> aliases;
};
static void need(bool ok,const char* reason) { if(!ok)throw runtime_error(reason); }
static string trim(const string& s) {
    for(unsigned char c:s)need(c<128,"Non-ASCII VCD requires review");
    const auto b=s.find_first_not_of(" \t\r\n");
    return b==string::npos?string():s.substr(b,s.find_last_not_of(" \t\r\n")-b+1);
}
static vector<string> words(const string& s) { istringstream in(s);vector<string> v;string w;while(in>>w)v.push_back(w);return v; }
static uint64_t integer(const string& s) {
    need(!s.empty(),"Missing unsigned integer");uint64_t n=0;
    for(char c:s){need(c>='0'&&c<='9',"Invalid unsigned integer");need(n<=(numeric_limits<uint64_t>::max()-(c-'0'))/10,"Integer overflow");n=n*10+c-'0';}return n;
}
static string quote(const string& s) {
    string result="\"";
    for(unsigned char c:s) {
        need(c>=32&&c<127,"Unprintable signal name");
        if(c=='\\'||c=='\"')result+='\\';result+=char(c);
    }
    return result+'"';
}
namespace mac {
const array<string,14> names={{"clk","rst_n","start_valid","start_ready","bias","shift",
    "in_valid","in_ready","x","w","out_valid","out_ready","result","saturated"}};
const array<unsigned,14> widths={{1,1,1,1,40,5,1,1,16,16,1,1,16,1}};
enum {CLK,RST,SV,SR,BIAS,SHIFT,IV,IR,X,W,OV,OR,RES,SAT};
struct Binding {unsigned lane,port,bit,offset;};
struct Lane {
    array<string,14> current,prior;
    array<vector<bool>,14> declared;
    array<uint64_t,14> unknown_edges={{}};
    uint64_t edges=0,starts=0,feeds=0,outputs=0,violations=0,first_violation=0;
    uint64_t first_feed=0,last_feed=0;
    uint64_t first_edge=0,last_edge=0,min_delta=0,max_delta=0,reset_edges=0;
    unsigned rises=0,accepted=0;bool busy=false;
    Lane(){for(unsigned p=0;p<14;++p){current[p]=prior[p]=string(widths[p],'?');declared[p].resize(widths[p]);}}
};
array<Lane,16> lanes;
unordered_map<string,vector<Binding>> watches;
uint64_t accepted_samples_unknown=0,ambiguous_controls=0;
static bool known(const string& s){return s.find_first_not_of("01")==string::npos;}
static void observe(const vector<string>& scope,const vector<string>& t) {
    string path;for(const auto& s:scope){if(!path.empty())path+='.';path+=s;}
    const string prefix="tb_top.u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems.u_arch03_accel.core.lanes[";
    if(path.compare(0,prefix.size(),prefix)!=0)return;
    auto close=path.find(']',prefix.size());need(close!=string::npos,"Malformed MAC lane scope");
    if(path.substr(close)!="].mac")return;
    unsigned lane=integer(path.substr(prefix.size(),close-prefix.size()));need(lane<16,"Unexpected MAC lane");
    auto found=find(names.begin(),names.end(),t[4]);if(found==names.end())return;
    unsigned port=found-names.begin(),width=integer(t[2]),low=0,high=width-1;
    need(t[1]!="real"&&t[1]!="realtime","Real-valued MAC port");
    if(t.size()==7){smatch m;need(regex_match(t[5],m,regex("\\[([0-9]+)(:([0-9]+))?\\]")),"Malformed MAC bit range");
        high=integer(m[1]);low=m[3].matched?integer(m[3]):high;
        need(high>=low&&high-low+1==width,"Unsupported MAC ascending/unequal range");
    }else need(t.size()==6&&width==1&&widths[port]==1,"MAC vector requires explicit bit range");
    need(high<widths[port],"MAC port width exceeded");
    for(unsigned bit=low;bit<=high;++bit){need(!lanes[lane].declared[port][bit],"Duplicate MAC port bit");
        lanes[lane].declared[port][bit]=true;watches[t[3]].push_back({lane,port,bit,bit-low});}
}
static void finish_header(){for(auto& lane:lanes)for(auto& port:lane.declared)
    need(all_of(port.begin(),port.end(),[](bool x){return x;}),"Missing MAC lane or port bit");}
static void snapshot(){for(auto& lane:lanes){lane.prior=lane.current;lane.rises=0;}}
static void update(const string& code,const string& raw,uint64_t width){
    auto f=watches.find(code);if(f==watches.end())return;
    need(raw.find_first_not_of("01xXzZ")==string::npos,"Unreviewed MAC value encoding");
    string v=raw;transform(v.begin(),v.end(),v.begin(),[](char c){return char(tolower(c));});
    need(!v.empty()&&v.size()<=width,"Malformed MAC width");
    // VCD short binary values zero-extend, except leading X/Z which extend X/Z.
    v=string(width-v.size(),v[0]=='x'||v[0]=='z'?v[0]:'0')+v;
    for(const auto& binding:f->second){auto& lane=lanes[binding.lane];char n=v[width-1-binding.offset];
        char& old=lane.current[binding.port][binding.bit];
        if(binding.port==CLK&&old=='0'&&n=='1')++lane.rises;
        old=n;
    }
}
static void violation(Lane& lane,uint64_t tick){if(!lane.violations)lane.first_violation=tick;++lane.violations;}
static int handshake(const string& valid,const string& ready){
    if(valid=="0"||ready=="0")return 0;
    if(valid=="1"&&ready=="1")return 1;
    return -1;
}
static void sample(uint64_t tick){
    for(auto& lane:lanes){
        need(lane.rises<=1,"Multiple MAC clock rises at same timestamp");
        if(!lane.rises)continue;
        need(lane.prior[CLK]=="0"&&lane.current[CLK]=="1","Ambiguous MAC clock ordering");
        if(lane.edges){uint64_t delta=tick-lane.last_edge;
            lane.min_delta=lane.edges==1?delta:min(lane.min_delta,delta);lane.max_delta=max(lane.max_delta,delta);
        }else lane.first_edge=tick;
        lane.last_edge=tick;++lane.edges;
        for(unsigned p=0;p<14;++p)if(!known(lane.prior[p]))++lane.unknown_edges[p];
        if(lane.prior[RST]=="0"){++lane.reset_edges;lane.busy=false;lane.accepted=0;continue;}
        if(lane.prior[RST]!="1"){++ambiguous_controls;violation(lane,tick);continue;}
        int start=handshake(lane.prior[SV],lane.prior[SR]);
        int feed=handshake(lane.prior[IV],lane.prior[IR]);
        int out=handshake(lane.prior[OV],lane.prior[OR]);
        for(int value:{start,feed,out})if(value<0){++ambiguous_controls;violation(lane,tick);}
        if(start==1){++lane.starts;if(lane.busy||feed==1||out==1)violation(lane,tick);
            lane.busy=true;lane.accepted=0;
            if(!known(lane.prior[BIAS])||!known(lane.prior[SHIFT])){++accepted_samples_unknown;violation(lane,tick);}}
        if(feed==1){if(!lane.feeds)lane.first_feed=tick;lane.last_feed=tick;++lane.feeds;
            if(!lane.busy||lane.accepted>=64||out==1)violation(lane,tick);++lane.accepted;
            if(!known(lane.prior[X])||!known(lane.prior[W])){++accepted_samples_unknown;violation(lane,tick);}}
        if(out==1){++lane.outputs;if(!lane.busy||lane.accepted!=64)violation(lane,tick);lane.busy=false;
            if(!known(lane.prior[RES])||!known(lane.prior[SAT])){++accepted_samples_unknown;violation(lane,tick);}}
    }
}
static void emit(){
    cout<<",\"mac_sampling\":{\"semantics\":\"pre_timestamp_values_on_observed_rising_edge\",\"accepted_samples_unknown\":"
        <<accepted_samples_unknown<<",\"ambiguous_controls\":"<<ambiguous_controls<<",\"lanes\":[";
    for(unsigned i=0;i<16;++i){if(i)cout<<",";const auto& l=lanes[i];
        cout<<"{\"lane\":"<<i<<",\"edges\":"<<l.edges<<",\"starts\":"<<l.starts<<",\"feeds\":"<<l.feeds
            <<",\"outputs\":"<<l.outputs<<",\"violations\":"<<l.violations
            <<",\"first_edge_tick\":"<<l.first_edge<<",\"last_edge_tick\":"<<l.last_edge
            <<",\"minimum_edge_interval_ticks\":"<<l.min_delta<<",\"maximum_edge_interval_ticks\":"<<l.max_delta
            <<",\"reset_edges\":"<<l.reset_edges
            <<",\"first_violation_tick\":"<<(l.violations?to_string(l.first_violation):"null")
            <<",\"first_feed_tick\":"<<(l.feeds?to_string(l.first_feed):"null")
            <<",\"last_feed_tick\":"<<(l.feeds?to_string(l.last_feed):"null")
            <<",\"unfinished_dot\":"<<(l.busy?"true":"false")<<",\"unknown_at_sampled_edges\":{";
        for(unsigned p=0;p<14;++p){if(p)cout<<",";cout<<quote(names[p])<<":"<<l.unknown_edges[p];}cout<<"}}";
    }cout<<"]}";
}
}
int main(int argc,char** argv) {
 try {
    need(argc==2,"Usage: activity_mac_use file.vcd");ifstream in(argv[1],ios::binary);need(bool(in),"Cannot open VCD");
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
          need(t.size()>=6&&t.back()=="$end","Malformed variable");auto width=integer(t[2]);need(width>0,"Zero width");
          need(scope.size()>=2&&scope[0]=="tb_top"&&scope[1]=="u_e203_soc_top","Signal outside selected SoC");
          unsigned mask=0;for(unsigned k=0;k<6;++k)if(find(scope.begin(),scope.end(),hierarchy[k])!=scope.end()){mask|=1U<<k;++roles[k];}
          string path;for(auto& part:scope){if(!path.empty())path+='.';path+=part;}path+='.'+t[4];
          for(size_t i=5;i+1<t.size();++i)path+=' '+t[i];
          Signal& s=ids[t[3]];need(!s.width||s.width==width,"Alias width mismatch");s.width=width;s.roles|=mask;s.aliases.push_back(path);++decl;
          mac::observe(scope,t);
        } else if(c=="$enddefinitions") {
          need(scope.empty()&&scale_fs&&decl,"Incomplete VCD hierarchy/timescale");for(auto n:roles)need(n>0,"Missing component hierarchy");mac::finish_header();header=false;
        } else need(c=="$date"||c=="$version"||c=="$comment","Unreviewed header command");
        continue;
      }
      if(line[0]=='#') { need(command.empty(),"Time inside incomplete dump command");auto n=integer(line.substr(1));need(n>=tick,"Time moved backwards");
        if(n>tick){if(active)mac::sample(tick);mac::snapshot();}tick=n;continue; }
      if(line[0]=='$') {
        auto t=words(line);const string& c=t[0];
        if(c=="$end") { need(!command.empty()&&t.size()==1,"Orphan dump end");command.clear();continue; }
        if(c=="$comment") {while(line.find("$end")==string::npos)need(bool(getline(in,line)),"Incomplete comment");continue;}
        need(command.empty()&&(c=="$dumpon"||c=="$dumpoff"||c=="$dumpvars"||c=="$dumpall"),"Unreviewed/nested body command");
        need(t.size()==1||(t.size()==2&&t[1]=="$end"),"Inline dump values unsupported");
        if(c=="$dumpon") {need(!active&&intervals==0,"Require single dumpon");active=true;begin=tick;}
        else if(c=="$dumpoff") {
          if(active){need(tick>begin,"Empty dump interval");mac::sample(tick);end=tick;++intervals;active=false;
            for(auto& pair:ids)if(pair.second.seen&&pair.second.bad)pair.second.unknown_ticks+=end-pair.second.last;
          }else need(tick==0,"Unexpected dumpoff");
        }
        command=t.size()==1?c:string();continue;
      }
      string value,code;char kind=line[0];
      if(string("01xXzZ").find(kind)!=string::npos) {value=line.substr(0,1);code=trim(line.substr(1));}
      else if(string("bBrR").find(kind)!=string::npos) {auto p=line.find_first_of(" \t",1);need(p!=string::npos,"Malformed vector/real");value=line.substr(1,p-1);code=trim(line.substr(p));need(code.find_first_of(" \t")==string::npos,"Malformed identifier");}
      else throw runtime_error("Unreviewed value encoding");
      auto found=ids.find(code);need(found!=ids.end(),"Value for undeclared signal");Signal& s=found->second;
      if(kind=='b'||kind=='B'){need(!value.empty()&&value.size()<=s.width,"Invalid vector width");need(value.find_first_not_of("01xXzZ")==string::npos,"Invalid vector digits");}
      if(active) {
        mac::update(code,value,s.width);
        ++changes;last=tick;bool bad=value.find_first_of("xXzZ")!=string::npos;
        if(kind=='r'||kind=='R') {char* after=nullptr;double v=strtod(value.c_str(),&after);need(after!=value.c_str()&&after==value.c_str()+value.size(),"Invalid real");bad=bad||!isfinite(v);}
        if(s.seen&&s.bad)s.unknown_ticks+=tick-s.last;
        if(!s.seen)s.first=tick;s.seen=true;s.last=tick;s.bad=bad;++s.records;
        if(bad){++unknown;if(s.unknown==0)s.first_unknown=tick;++s.unknown;s.last_unknown=tick;
          if(tick==begin)++s.initial_unknown;else ++s.later_unknown;
        }
        for(unsigned k=0;k<6;++k)if(s.roles&(1U<<k))++events[k];
      }
    }
    need(in.eof(),"VCD input read error");need(!header&&!active&&command.empty()&&intervals==1,"Require one complete task interval");
    need(changes&&last>begin,"No active task transitions");for(auto n:events)need(n>0,"Missing component activity");
    cout<<"{\"schema\":\"activity_unknown_mac_stream_v1\",\"scale_fs\":"<<scale_fs<<",\"begin_tick\":"<<begin<<",\"end_tick\":"<<end
        <<",\"signal_declarations\":"<<decl<<",\"unique_identifiers\":"<<ids.size()
        <<",\"active_value_records\":"<<changes<<",\"unknown_value_records\":"<<unknown;
    for(unsigned mode=0;mode<2;++mode){cout<<",\""<<(mode?"component_value_records":"component_declarations")<<"\":{";for(unsigned k=0;k<6;++k){if(k)cout<<",";cout<<quote(names[k])<<":"<<(mode?events[k]:roles[k]);}cout<<"}";}
    vector<string> selected;uint64_t at_begin=0,later=0,affected=0,missing=0,persistent=0;
    for(auto& pair:ids){auto& s=pair.second;at_begin+=s.initial_unknown;later+=s.later_unknown;
      if(s.unknown)++affected;if(!s.seen||s.first>begin)++missing;if(s.bad)++persistent;
      need(s.unknown_ticks<=end-begin,"Invalid unknown duration");
      if(s.unknown||!s.seen||s.first>begin)selected.push_back(pair.first);
    }
    sort(selected.begin(),selected.end());
    cout<<",\"unknown_records_at_begin\":"<<at_begin<<",\"unknown_records_after_begin\":"<<later
        <<",\"unknown_identifiers\":"<<affected<<",\"identifiers_without_initial_observation\":"<<missing
        <<",\"unknown_identifiers_at_end\":"<<persistent<<",\"signals\":[";
    bool firstrow=true;
    for(auto& code:selected){auto& s=ids.at(code);if(!firstrow)cout<<",";firstrow=false;
      cout<<"{\"identifier\":"<<quote(code)<<",\"width\":"<<s.width<<",\"aliases\":[";
      for(size_t i=0;i<s.aliases.size();++i){if(i)cout<<",";cout<<quote(s.aliases[i]);}
      cout<<"],\"roles\":[";bool firstrole=true;for(unsigned k=0;k<6;++k)if(s.roles&(1U<<k)){if(!firstrole)cout<<",";firstrole=false;cout<<quote(names[k]);}
      cout<<"],\"value_records\":"<<s.records<<",\"unknown_records\":"<<s.unknown
          <<",\"unknown_records_at_begin\":"<<s.initial_unknown<<",\"unknown_records_after_begin\":"<<s.later_unknown
          <<",\"first_observation_tick\":"<<(s.seen?to_string(s.first):"null")
          <<",\"unobserved_prefix_ticks\":"<<(s.seen?s.first-begin:end-begin)
          <<",\"first_unknown_tick\":"<<(s.unknown?to_string(s.first_unknown):"null")
          <<",\"last_unknown_tick\":"<<(s.unknown?to_string(s.last_unknown):"null")
          <<",\"any_unknown_ticks\":"<<s.unknown_ticks<<",\"unknown_at_end\":"<<(s.bad?"true":"false")<<"}";
    }
    cout<<"]";mac::emit();cout<<"}\n";return 0;
 } catch(const exception& e) {cerr<<"MAC_USE_ACTIVITY_AUDIT_ERROR "<<e.what()<<"\n";return 1;}
}
