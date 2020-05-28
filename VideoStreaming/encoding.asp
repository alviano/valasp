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

:~ assign(USER_ID,_,_,BITRATE,SAT_VALUE), user(USER_ID,_,_,_,BEST_SAT,_).
[BEST_SAT-SAT_VALUE@1,USER_ID,assign]

% #show assign/5.
