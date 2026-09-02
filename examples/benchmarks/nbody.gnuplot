set terminal png size 1024,768
set output "nbody.png"

stats "nbody.data"

plot for [i=1:(STATS_columns-1)] "nbody.data" using i:i+1 with lines notitle
