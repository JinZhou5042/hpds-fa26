
PROGRAMS=simple-parallel simple-parallel-for simple-parallel-single simple-parallel-section

all: $(PROGRAMS)

%: %.c
	g++ $< -o $@ -fopenmp -O1

clean:
	rm -f $(PROGRAMS)

