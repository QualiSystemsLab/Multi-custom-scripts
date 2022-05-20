#!/bin/bash -xe
touch /git/test.log
function func1 {
   fun="$1"
   book="$2"
   echo "func=$fun,book=$book" >> /git/logs.log 2>&1
   echo "func" >> /git/test.log
}

function func2 {
   fun2="$1"
   book2="$2"
   echo "func2=$fun2,book2=$book2" >> /git/logs.log 2>&1
   echo "func2" >> /git/test.log
}

function func3_echo {
   echo "func3 $1" >> /git/logs.log 2>&1
   echo "func3 $2" >> /git/test.log
}