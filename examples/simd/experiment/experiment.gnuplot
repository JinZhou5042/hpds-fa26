# To plot: 
#    module load gnuplot
#    gnuplot experiment.gnuplot
#    (produces experiment.png)

set terminal pngcairo font "Arial, 24" size 1024, 480
set output "experiment.png"

set xlabel "Array Size (bytes)"
set ylabel "Runtime (s)"
set key top left

plot "baseline.data" using 2:4 with linespoints title "Baseline", "improved.data" using 2:4 with linespoints title "SIMD Intrinsics"
