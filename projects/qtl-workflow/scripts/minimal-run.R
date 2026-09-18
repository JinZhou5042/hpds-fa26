# Run with: Rscript scripts/minimal-run.R
script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
project_dir <- normalizePath(file.path(dirname(sub("^--file=", "", script_arg)), ".."))
result_dir <- file.path(project_dir, "results")
.libPaths(c(file.path(project_dir, ".R-library"), .libPaths()))
library(qtl)
dir.create(result_dir, showWarnings = FALSE)
set.seed(20260907)
started <- proc.time()
cross <- read.cross(format = "csv",
    file = file.path(project_dir, "data", "Dd2xHB3rQTL_CollateralSensitivity_Indexes.csv"),
    na.strings = "NA", genotypes = c(0, 1))
print(summary(cross))
cat("Phenotype:", colnames(cross$pheno)[2], "\n")
out <- scanone(cross, method = "hk", pheno.col = 2, batchsize = 37)
perms <- scanone(cross, method = "hk", n.perm = 10,
                 verbose = FALSE, pheno.col = 2, batchsize = 37)
stopifnot(nrow(out) > 0, all(is.finite(out$lod)),
          nrow(perms) == 10, all(is.finite(perms)))
write.csv(out, file.path(result_dir, "scanone.csv"))
write.csv(perms, file.path(result_dir, "permutations.csv"))
png(file.path(result_dir, "qtl-scan.png"), width = 1200, height = 800)
plot(out, main = paste(colnames(cross$pheno)[2], "QTL scan"))
dev.off()
peak <- out[which.max(out$lod), , drop = FALSE]
cat("Peak:\n")
print(peak)
cat("Elapsed seconds:", (proc.time() - started)[["elapsed"]], "\n")
print(sessionInfo())
cat("PASS: single-phenotype scan, 10 permutations, and PNG output.\n")
