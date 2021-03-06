#!/bin/bash

. shellscripts/querylibrary.sh # import custom functions

FP1='{"EE":[0,0],"Rp":[1,1]}' 
FP2='{"EE":[1,8],"Rp":[0,0]}'
python $DSGRN/software/FPQuery/FPQuery2.py $DATABASEFILE DoubleFP $FP1 $FP2 > $DATABASEDIR/query$NETWORKID.txt
NUMFP=`getcountuniquelines $DATABASEDIR/query$NETWORKID.txt`
rm $DATABASEDIR/query$NETWORKID.txt 
echo "DoubleFPQuery:$FP1 $FP2 __ DoubleFPQueryParameterCount:"$NUMFP #split entries by **