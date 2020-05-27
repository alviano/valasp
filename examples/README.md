# Examples

## Birthday

```shell script
(valasp) $ python -m valasp examples/bday.yaml examples/bday.valid.asp 
ALL VALID!
==========
Answer: bday(sofia,(2019,6,25)) bday(leonardo,(2018,2,1))
==========
```

```shell script
(valasp) $ python -m valasp examples/bday.yaml examples/bday.invalid.asp 
VALIDATION FAILED
=================
Invalid instance of bday:
    in constructor of bday
    in constructor of date
  with error: expecting arity 3 for TUPLE, but found 2; invalid term (1982,123) in atom bday(bigel,(1982,123))
=================
```

## Video Streaming
```shell script
(valasp) $ python -m valasp examples/video_streaming.yaml examples/
bday.invalid.asp              bday.yaml                     video_streaming.encoding.asp  video_streaming.yaml          
bday.valid.asp                README.md                     video_streaming.instance.asp  
(valasp) $ python -m valasp examples/video_streaming.yaml examples/video_streaming.encoding.asp examples/video_streaming.instance.asp 
VALIDATION FAILED
=================
sum of value in predicate obj may exceed 2147483647
=================
```
