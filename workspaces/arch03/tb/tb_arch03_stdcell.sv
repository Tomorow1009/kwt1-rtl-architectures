`timescale 1ns/1ps
// Same bench for an explicitly marked local substitute and the server vendor
// functional models. This checks functions/ports, never delay or clock signoff.
module tb_arch03_stdcell;
    reg a=0,b=0,s=0,ck=0,e=0,te=0;
    wire ybuf,yclkbuf,yand,ynand,ymux,yinv,yor,ygate,yxor,ylogicnand,ynor;
    integer n,gate_checks=0;
    BUFV4_12TR40 m0(.I(a),.Z(ybuf));
    CLKBUFV4_12TR40 m1(.I(a),.Z(yclkbuf));
    CLKAND2V4_12TR40 m2(.A1(a),.A2(b),.Z(yand));
    CLKNAND2V4_12TR40 m3(.A1(a),.A2(b),.ZN(ynand));
    CLKMUX2V4_12TR40 m4(.I0(a),.I1(b),.S(s),.Z(ymux));
    INV4_12TR40 m5(.I(a),.ZN(yinv));
    OR2V4_12TR40 m6(.A1(a),.A2(b),.Z(yor));
    CLKLANAQV4_12TR40 m7(.CK(ck),.E(e),.TE(te),.Q(ygate));
    CLKXOR2V4_12TR40 m8(.A1(a),.A2(b),.Z(yxor));
    NAND2V4_12TR40 m9(.A1(a),.A2(b),.ZN(ylogicnand));
    NOR2V4_12TR40 m10(.A1(a),.A2(b),.ZN(ynor));
    task check_gate(input expected);
        begin #2;if(ygate!==expected)$fatal(1,"Gate state mismatch ck=%b e=%b te=%b got=%b expected=%b",ck,e,te,ygate,expected);gate_checks=gate_checks+1;end
    endtask
    initial begin
        for(n=0;n<8;n=n+1)begin
            {s,b,a}=n;#2;
            if(ybuf!==a || yclkbuf!==a || yand!==(a&b) || ynand!==~(a&b) ||
               ymux!==(s ? b : a) || yinv!==~a || yor!==(a|b) ||
               yxor!==(a^b) || ylogicnand!==~(a&b) || ynor!==~(a|b))
                $fatal(1,"Combinational standard-cell binding mismatch pattern=%0d",n);
        end
        check_gate(0);
        ck=1;check_gate(0);
        e=1;check_gate(0); // Changing E during high clock must not open the gate.
        ck=0;check_gate(0);
        ck=1;check_gate(1);
        e=0;check_gate(1); // Changing E during high clock must not truncate a pulse.
        ck=0;check_gate(0);
        ck=1;check_gate(0);
        te=1;check_gate(1); // The verified cell has post-latch test control.
        te=0;check_gate(0);
        ck=0;te=1;check_gate(0);
        ck=1;check_gate(1);
        $display("ARCH03_STDCELL_PASS combinational_patterns=8 gate_checks=%0d types=11 functional_only=true",gate_checks);
        $finish;
    end
    initial begin #1000;$fatal(1,"Standard-cell test timeout");end
endmodule
