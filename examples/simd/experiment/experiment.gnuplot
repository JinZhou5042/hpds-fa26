set terminal png
set output "experiment.png"

plot "baseline.data" using 2:4 with boxes, "improved.data" using 2:4 with boxes
