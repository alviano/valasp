% max_representations(19).
% fraction_user(19).
% global_capacity(100000).

{
        r(VIDEO,RESOLUTION,BITRATE,SAT_VALUE) :
        f(VIDEO,RESOLUTION,BITRATE,SAT_VALUE),
        user(_,VIDEO,RESOLUTION,BANDWIDTH,MAX_SAT,MAX_BIT),BITRATE <= MAX_BIT
} = M :- max_representations(M).

{
    assign(USER_ID,VIDEO_TYPE,RESOLUTION,BITRATE,SAT):
    f(VIDEO_TYPE,RESOLUTION,BITRATE,SAT),
    BITRATE <= MAX_BIT
}
:- user(USER_ID,VIDEO_TYPE,RESOLUTION,BANDWIDTH,MAX_SAT,MAX_BIT).

:- assign(USER_ID,VIDEO_TYPE,RESOLUTION,BITRATE,SAT), not r(VIDEO_TYPE,RESOLUTION,BITRATE,SAT).

:- global_capacity(G), G < #sum{BITRATE,USER_ID : assign(USER_ID,_,_,BITRATE,_)}.
:- fraction_user(F), F > #count{USER_ID : assign(USER_ID,_,_,_,_)}.

:- #sum{BEST_SAT-SAT_VALUE,USER_ID : assign(USER_ID,_,_,BITRATE,SAT_VALUE), user(USER_ID,_,_,_,BEST_SAT,_)} > B, bound(B).

assign(0,"Video",1080,2350,840073136).
assign(1,"Cartoon",360,750,978975156).
assign(2,"Cartoon",360,750,978975156).
assign(3,"Cartoon",360,750,978975156).
assign(4,"Documentary",720,5850,995511401).
assign(5,"Documentary",720,5850,995511401).
assign(6,"Sport",1080,7300,956558668).
assign(7,"Cartoon",224,750,992011820).
assign(8,"Video",720,1850,917420577).
assign(9,"Cartoon",224,750,992011820).
assign(10,"Sport",360,200,165121752).
assign(11,"Video",224,450,891372336).
assign(12,"Video",224,450,891372336).
assign(13,"Cartoon",224,750,992011820).
assign(15,"Video",720,1850,917420577).
assign(16,"Cartoon",360,750,978975156).
assign(17,"Sport",224,1800,986664359).
assign(18,"Sport",360,200,165121752).
assign(19,"Video",720,1850,917420577).
assign(20,"Sport",1080,7300,956558668).
assign(21,"Cartoon",224,750,992011820).
assign(22,"Sport",360,200,165121752).
assign(23,"Documentary",360,250,834937238).
assign(24,"Sport",360,200,165121752).
assign(26,"Sport",224,1800,986664359).
assign(27,"Cartoon",224,750,992011820).
assign(28,"Documentary",360,250,834937238).
assign(29,"Video",224,450,891372336).
assign(30,"Sport",224,1800,986664359).
assign(31,"Video",360,600,873263844).
assign(32,"Video",224,450,891372336).
assign(33,"Video",360,600,873263844).
assign(34,"Video",360,600,873263844).
assign(35,"Documentary",360,250,834937238).
assign(36,"Cartoon",224,750,992011820).
assign(37,"Video",360,600,873263844).
assign(38,"Video",720,1850,917420577).
assign(39,"Cartoon",360,750,978975156).
assign(40,"Video",224,450,891372336).
assign(41,"Cartoon",360,750,978975156).
assign(42,"Video",720,1850,917420577).
assign(43,"Cartoon",360,750,978975156).
assign(44,"Video",224,450,891372336).
assign(45,"Sport",1080,7300,956558668).
assign(46,"Documentary",1080,7250,999893906).
assign(47,"Documentary",360,250,834937238).
assign(48,"Cartoon",360,750,978975156).
assign(49,"Video",224,450,891372336).

:~ assign(USER_ID,_,_,BITRATE,SAT_VALUE), user(USER_ID,_,_,_,BEST_SAT,_).
[BEST_SAT-SAT_VALUE@1,USER_ID,assign]

% #show assign/5.
