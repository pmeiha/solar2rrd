# two scripts to collect data from solarmanager

# get data for one day
/home/pmei/Projekt/solar2rrd/s2rrd.py -h
usage: s2rrd.py [-h] [-d DAY] [-m MONTH] [-y YEAR] [-r REQUESTINTERVAL] [-l]

get solar data

options:
  -h, --help            show this help message and exit
  -d DAY, --day DAY     day
  -m MONTH, --month MONTH
                        month
  -y YEAR, --year YEAR  year
  -r REQUESTINTERVAL, --requestinterval REQUESTINTERVAL
                        time between cloud requests
  -l, --loglevel        loglevel default warning or higher

# example 
/home/pmei/Projekt/solar2rrd/.venv/bin/python /home/pmei/Projekt/solar2rrd/s2rrd.py -y 2025 -m 1 -d 1

# summarize
/home/pmei/Projekt/solar2rrd/s2sum.py -h
usage: s2sum.py [-h] [-d DIRECTORY] [-s FILESTART] [-e FILEEND] [-o OUTFILE] [-a] [-l]

summarize solar data

options:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        directory to search for file
  -s FILESTART, --filestart FILESTART
                        start for the filenames
  -e FILEEND, --fileend FILEEND
                        end of the filename
  -o OUTFILE, --outfile OUTFILE
                        output file for the summary
  -a, --add             add the last line from all the files
  -l, --loglevel        loglevel default warning or higher

# summarize all day from one month
/home/pmei/Projekt/solar2rrd/s2sum.py -o data-out/2025-02-sum.csv -e min.csv -s 2025-02 -d data-in -a

# summarize all month to one summary file
/home/pmei/Projekt/solar2rrd/s2sum.py -o data-out/summary.csv -e sum.csv -s '20' -d data-out