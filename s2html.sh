#!/usr/bin/bash
#

datadir="/data/solar2rrd"
mainpath="s2.html"
pngdir="${datadir}/png"
htmlfile="${pngdir}/s2.html"
tagpath=""
rrdfile="${datadir}/rrd/s2.rrd"
monthfile=0

#-----------------------------------------------------------------------------------------------------
# print usage
#-----------------------------------------------------------------------------------------------------
function usage {

cat <<END

usage: $0  [-d directory] [-H filename] [-p tagpath] [-m] [-h]"
     -h           -> these help text
     -d directory -> data directory for the resulting graph (default $datadir)
     -H filename  -> data directory for the resulting graph (default $htmlfile)
     -p tagpath   -> html path for the resulting graph (default $tagpath)
     -m           -> genarate also week and month ... graph (default day graphs only)
     
END

}

#-----------------------------------------------------------------------------------------------------
# get cli parameter
#-----------------------------------------------------------------------------------------------------
function getparameter {

  while getopts "h:d:H:p:m" option; do
    case $option in
      d ) datadir="$OPTARG/" ;;
      p ) tagpath="$OPTARG/" ;;
      H ) htmlfile=$OPTARG ;;
      m ) monthfile=1 ;;
      h|* ) usage
          return 1
    esac
  done

  shift $(($OPTIND - 1))

  return 0
}

#-----------------------------------------------------------------------------------------------------
# write html haeder
#-----------------------------------------------------------------------------------------------------
function htmlHeader {

local outfile=$1

cat<<'END' >$outfile
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<HTML>
 <HEAD>
  <TITLE>PV-Data</TITLE>
 </HEAD>
 <BODY BGCOLOR="#F0F0F0">
END

}

#-----------------------------------------------------------------------------------------------------
# write html trailer
#-----------------------------------------------------------------------------------------------------
function htmlEnd {

local outfile=$1

cat<<'END' >>$outfile
 </BODY>
</HTML>
END

}

#-----------------------------------------------------------------------------------------------------
# generate infra graph
#-----------------------------------------------------------------------------------------------------
function createInfraPng {

    local start=$1
    local end=$2
    local step=$3
    local pngfile=$4

    tstart=$( date -d "@$start")
    tend=$( date -d "@$end")

    rrdtool graph ${pngfile} \
        --start "$start" \
        --end "$end" \
        --title "$tstart - $tend" \
        --vertical-label=Wh \
        --upper-limit=18000 \
        --step $step \
        --height=500 \
        --width=1500 \
        --rigid \
        "DEF:PV-raw=$rrdfile:PV:AVERAGE:step=$step" \
        "DEF:Ni-raw=$rrdfile:Ni:AVERAGE:step=$step" \
        "DEF:Ne-raw=$rrdfile:Ne:AVERAGE:step=$step" \
        "DEF:SoBat-raw=$rrdfile:SoBat:AVERAGE:step=$step" \
        "DEF:NeBat-raw=$rrdfile:NeBat:AVERAGE:step=$step" \
        "DEF:SoNe-raw=$rrdfile:SoNe:AVERAGE:step=$step" \
        "DEF:BatNe-raw=$rrdfile:BatNe:AVERAGE:step=$step" \
        "DEF:Netto-raw=$rrdfile:Netto:AVERAGE:step=$step" \
        "CDEF:PV=PV-raw,3600,*" \
        "CDEF:Ni=Ni-raw,3600,*" \
        "CDEF:Ne=Ne-raw,3600,*" \
        "CDEF:Netto=Netto-raw,3600,*" \
        "CDEF:SoBat=SoBat-raw,3600,*" \
        "CDEF:NeBat=NeBat-raw,3600,*" \
        "CDEF:SoNe=SoNe-raw,3600,*" \
        "CDEF:BatNe=BatNe-raw,3600,*" \
        "CDEF:Self1=PV,Netto,-" \
        "CDEF:Self=Self1,0,GE,Netto,PV,IF" \
        "AREA:Netto#003dff:Verbrauch" \
        "AREA:Self#007215:EigenVerbrauch" \
        "AREA:SoBat#fdce00:SoBat:STACK" \
        "AREA:SoNe#b1fd00:SoNe:STACK" \
        "AREA:Ni#FF0000:NetzImport" \
        "AREA:NeBat#dc4646:NeBat" \
        "AREA:BatNe#00fd5c:BatNe" \
        "LINE:PV#002a08:"

}

#-----------------------------------------------------------------------------------------------------
# generate Device graph
#-----------------------------------------------------------------------------------------------------
function createDevPng {

    local start=$1
    local end=$2
    local step=$3
    local pngfile=$4
    local dev=$5
    local label=$6
    local max=$7

    tstart=$(date -d "@$start")
    tend=$(date -d "@$end")

    rrdtool graph ${pngfile} \
        --start "$start" \
        --end "$end" \
        --title "$tstart - $tend" \
        --step 1 \
        --height=500 \
        --width=1500 \
        --vertical-label=W \
        --upper-limit=${max} \
        --rigid \
        "DEF:NN-raw=$rrdfile:NN${dev}:MAX:step=$step" \
        "DEF:NH-raw=$rrdfile:NH${dev}:MAX:step=$step" \
        "DEF:SN-raw=$rrdfile:SN${dev}:MAX:step=$step" \
        "DEF:SH-raw=$rrdfile:SH${dev}:MAX:step=$step" \
        "DEF:BN-raw=$rrdfile:BN${dev}:MAX:step=$step" \
        "DEF:BH-raw=$rrdfile:BH${dev}:MAX:step=$step" \
        "CDEF:Netz=NN-raw,NH-raw,+,3600,*," \
        "CDEF:Sonne=SN-raw,SH-raw,+,3600,*," \
        "CDEF:Battery=BN-raw,BH-raw,+,3600,*," \
        "AREA:Sonne#ffdf36:${label} Sonne" \
        "AREA:Battery#4fd5a9:${label} Batterie:STACK" \
        "AREA:Netz#ff015b:${label} Netz:STACK" \
        "LINE:Sonne#776816" \
        "LINE:Battery#2a785f::STACK" \
        "LINE:Netz#771638::STACK"

}

######################################################################################################
# start main
######################################################################################################

getparameter $* || exit 1

end="$(date '+%s')"
std=$(date -d "-1 day -1 hour" '+%s')
stw=$(date -d "-1 week -1 hour" '+%s')
stm=$(date -d "-1 month -1 hour" '+%s')
stj=$(date -d "-1 year -1 hour" '+%s')

echo "$(date) generate infra"
createInfraPng "$std" "$end" 60   "${pngdir}/s2infra_day.png"
if [ $monthfile -eq 1 ]
then
  createInfraPng "$stw" "$end" 600  "${pngdir}/s2infra_week.png"
  createInfraPng "$stm" "$end" 600  "${pngdir}/s2infra_mnt.png"
  createInfraPng "$stj" "$end" 3600 "${pngdir}/s2infra_year.png"
fi

htmlmain="$htmlfile"

htmlHeader $htmlfile

echo "<p>Tages Graphen</p>" >>$htmlfile

echo "<IMG SRC='${tagpath}s2infra_day.png' ALT='Verbrauchsgraph'><br>" >>$htmlfile
echo "<IMG SRC='${tagpath}s2infra_week.png' ALT='Verbrauchsgraph'><br>" >>$htmlfile
echo "<IMG SRC='${tagpath}s2infra_mnt.png' ALT='Verbrauchsgraph'><br>" >>$htmlfile
echo "<IMG SRC='${tagpath}s2infra_year.png' ALT='Verbrauchsgraph'><br>" >>$htmlfile

echo "<a href='${tagpath}s2Re.html'>RestVerbraucher        ${tagpath}s2Re.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2Wp.html'>Wärmepumpe             ${tagpath}s2Wp.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2La.html'>Ladestation            ${tagpath}s2La.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2IT.html'>IT                     ${tagpath}s2IT.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2Lk.html'>Luftentfewuchter Keller${tagpath}s2Lk.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2Bg.html'>Bewässerung Garten     ${tagpath}s2Bg.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2Bt.html'>Bewässerung Topf       ${tagpath}s2Bt.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2Bh.html'>Begleitheizung         ${tagpath}s2Bh.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2Zh.html'>Zusatzheizung          ${tagpath}s2Zh.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2W1.html'>Weinacht1              ${tagpath}s2W1.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2W2.html'>Weihnacht2             ${tagpath}s2W2.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2Wa.html'>Waschen                ${tagpath}s2Wa.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2Tr.html'>Trocknen               ${tagpath}s2Tr.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2Fe.html'>Frigo Estrich          ${tagpath}s2Fe.html</a><br>" >>$htmlfile
echo "<a href='${tagpath}s2Fk.html'>Frigo Keller           ${tagpath}s2Fk.html</a><br>" >>$htmlfile

htmlEnd $htmlfile

echo "$(date) generate dev day"
createDevPng "$std" "$end" 60 "${pngdir}/s2Re_day.png"   "Rest" "RestVerbraucher"         "11000"
createDevPng "$std" "$end" 60 "${pngdir}/s2Wp_day.png"   "Wp"   "Wärmepumpe"              "5000"
createDevPng "$std" "$end" 60 "${pngdir}/s2La_day.png"   "La"   "Ladestation"             "13000"
createDevPng "$std" "$end" 60 "${pngdir}/s2IT_day.png"   "IT"   "IT"                      "800"
createDevPng "$std" "$end" 60 "${pngdir}/s2Lk_day.png"   "Lk"   "Luftentfewuchter Keller" "500"
createDevPng "$std" "$end" 60 "${pngdir}/s2Bg_day.png"   "Bg"   "Bewässerung Garten"      "100"
createDevPng "$std" "$end" 60 "${pngdir}/s2Bt_day.png"   "Bt"   "Bewässerung Topf"        "20"
createDevPng "$std" "$end" 60 "${pngdir}/s2Bh_day.png"   "Bh"   "Begleitheizung"          "1000"
createDevPng "$std" "$end" 60 "${pngdir}/s2Zh_day.png"   "Zh"   "Zusatzheizung"           "3000"
createDevPng "$std" "$end" 60 "${pngdir}/s2W1_day.png"   "W1"   "Weinacht1"               "1000"
createDevPng "$std" "$end" 60 "${pngdir}/s2W2_day.png"   "W2"   "Weihnacht2"              "1000"
createDevPng "$std" "$end" 60 "${pngdir}/s2Wa_day.png"   "Wa"   "Waschen"                 "2800"
createDevPng "$std" "$end" 60 "${pngdir}/s2Tr_day.png"   "Tr"   "Trocknen"                "2800"
createDevPng "$std" "$end" 60 "${pngdir}/s2Fe_day.png"   "Fe"   "Frigo Estrich"           "500"
createDevPng "$std" "$end" 60 "${pngdir}/s2Fk_day.png"   "Fk"   "Frigo Keller"            "500"

if [ $monthfile -eq 1 ]
then
  echo "$(date) generate dev week"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2Re_week.png"   "Rest" "RestVerbraucher"         "11000"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2Wp_week.png"   "Wp"   "Wärmepumpe"              "5000"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2La_week.png"   "La"   "Ladestation"             "13000"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2IT_week.png"   "IT"   "IT"                      "800"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2Lk_week.png"   "Lk"   "Luftentfewuchter Keller" "500"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2Bg_week.png"   "Bg"   "Bewässerung Garten"      "100"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2Bt_week.png"   "Bt"   "Bewässerung Topf"        "20"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2Bh_week.png"   "Bh"   "Begleitheizung"          "1000"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2Zh_week.png"   "Zh"   "Zusatzheizung"           "3000"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2W1_week.png"   "W1"   "Weinacht1"               "1000"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2W2_week.png"   "W2"   "Weihnacht2"              "1000"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2Wa_week.png"   "Wa"   "Waschen"                 "2800"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2Tr_week.png"   "Tr"   "Trocknen"                "2800"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2Fe_week.png"   "Fe"   "Frigo Estrich"           "500"
  createDevPng "$stw" "$end" 600 "${pngdir}/s2Fk_week.png"   "Fk"   "Frigo Keller"            "500"

  echo "$(date) generate dev month"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2Re_mnt.png"   "Rest" "RestVerbraucher"         "11000"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2Wp_mnt.png"   "Wp"   "Wärmepumpe"              "5000"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2La_mnt.png"   "La"   "Ladestation"             "13000"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2IT_mnt.png"   "IT"   "IT"                      "800"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2Lk_mnt.png"   "Lk"   "Luftentfewuchter Keller" "500"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2Bg_mnt.png"   "Bg"   "Bewässerung Garten"      "100"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2Bt_mnt.png"   "Bt"   "Bewässerung Topf"        "20"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2Bh_mnt.png"   "Bh"   "Begleitheizung"          "1000"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2Zh_mnt.png"   "Zh"   "Zusatzheizung"           "3000"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2W1_mnt.png"   "W1"   "Weinacht1"               "1000"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2W2_mnt.png"   "W2"   "Weihnacht2"              "1000"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2Wa_mnt.png"   "Wa"   "Waschen"                 "2800"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2Tr_mnt.png"   "Tr"   "Trocknen"                "2800"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2Fe_mnt.png"   "Fe"   "Frigo Estrich"           "500"
  createDevPng "$stm" "$end" 3600 "${pngdir}/s2Fk_mnt.png"   "Fk"   "Frigo Keller"            "500"
fi

for dev in "s2Re" \
           "s2Wp" \
           "s2La" \
           "s2IT" \
           "s2Lk" \
           "s2Bg" \
           "s2Bt" \
           "s2Bh" \
           "s2Zh" \
           "s2W1" \
           "s2W2" \
           "s2Wa" \
           "s2Tr" \
           "s2Fe" \
           "s2Fk"
do

    htmlfile="${pngdir}/${dev}.html"

    htmlHeader $htmlfile
    echo "<a href='${mainpath}'>Zurück</a><br>" >>$htmlfile
    echo "<IMG SRC='${tagpath}${dev}_day.png' ALT='Verbrauchsgraph'><br>" >>$htmlfile
    echo "<a href='${mainpath}'>Zurück</a><br>" >>$htmlfile
    echo "<IMG SRC='${tagpath}${dev}_week.png' ALT='Verbrauchsgraph'><br>" >>$htmlfile
    echo "<a href='${mainpath}'>Zurück</a><br>" >>$htmlfile
    echo "<IMG SRC='${tagpath}${dev}_mnt.png' ALT='Verbrauchsgraph'><br>" >>$htmlfile
    echo "<a href='${mainpath}'>Zurück</a><br>" >>$htmlfile
    
    htmlEnd $htmlfile
    
done                    

echo "$(date) end"

