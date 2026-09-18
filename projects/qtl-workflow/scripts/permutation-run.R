# Run with: Rscript scripts/permutation-run.R
script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
project_dir <- normalizePath(file.path(dirname(sub("^--file=", "", script_arg)), ".."))
result_dir <- file.path(project_dir, "results", "permutation-1000")
.libPaths(c(file.path(project_dir, ".R-library"), .libPaths()))
library(qtl)
dir.create(result_dir, recursive = TRUE, showWarnings = FALSE)
set.seed(20260907)
started <- proc.time()
cross <- read.cross(format = "csv",
    file = file.path(project_dir, "data", "Dd2xHB3rQTL_CollateralSensitivity_Indexes.csv"),
    na.strings = "NA", genotypes = c(0, 1))
print(summary(cross))
cat("Phenotype:", colnames(cross$pheno)[2], "\n")
out <- scanone(cross, method = "hk", pheno.col = 2, batchsize = 37)
perm_started <- proc.time()
perms <- scanone(cross, method = "hk", n.perm = 1000,
                 verbose = FALSE, pheno.col = 2, batchsize = 37)
perm_seconds <- (proc.time() - perm_started)[["elapsed"]]
cat("Permutation elapsed seconds:", perm_seconds, "\n")
thresholds <- summary(perms, alpha = c(0.37, 0.05, 0.01))
print(thresholds)
stopifnot(all(is.finite(thresholds)))
write.csv(thresholds, file.path(result_dir, "thresholds.csv"))
stopifnot(nrow(out) > 0, all(is.finite(out$lod)),
          nrow(perms) == 1000, all(is.finite(perms)))
write.csv(out, file.path(result_dir, "scanone.csv"))
write.csv(perms, file.path(result_dir, "permutations.csv"))
png(file.path(result_dir, "qtl-scan.png"), width = 1200, height = 800)
plot(out, main = paste(colnames(cross$pheno)[2], "QTL scan"),
     ylim = c(0, max(out$lod, thresholds) * 1.15))
abline(h = as.numeric(thresholds), col = c("steelblue", "darkorange", "red"), lty = c(2, 3, 4))
legend("topright", legend = paste0("alpha = ", c(0.37, 0.05, 0.01),
       ", LOD = ", round(as.numeric(thresholds), 3)),
       col = c("steelblue", "darkorange", "red"), lty = c(2, 3, 4), bty = "n")
dev.off()
peak <- out[which.max(out$lod), , drop = FALSE]
cat("Peak:\n")
print(peak)
cat("Elapsed seconds:", (proc.time() - started)[["elapsed"]], "\n")
print(sessionInfo())
cat("PASS: single-phenotype scan, 1000 permutations, and PNG output.\n")
