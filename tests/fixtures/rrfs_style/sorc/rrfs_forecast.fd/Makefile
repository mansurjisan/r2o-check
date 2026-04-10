FC = $(FC)
FFLAGS = -O2

all: rrfs_forecast

debug: FFLAGS = -g -check all -ftrapuv
debug: rrfs_forecast

rrfs_forecast: main.f90
	$(FC) $(FFLAGS) -o $@ $<

install: rrfs_forecast
	mkdir -p ../../exec
	cp rrfs_forecast ../../exec/

clean:
	rm -f rrfs_forecast *.o *.mod
