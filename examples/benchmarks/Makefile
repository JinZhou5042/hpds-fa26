all: matrix nbody heat fractal nbody

fractal: fractal.c
	gcc fractal.c -o fractal -lm -g -O1

heat: heat.c
	g++ heat.c -o heat -lm -g -O1

nbody: nbody.c
	g++ nbody.c -o nbody -lm -g -O1

matrix: matrix.c
	g++ matrix.c -o matrix -lm -g -O1

clean:
	rm -f matrix nbody heat fractal
