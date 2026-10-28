# Sonny Vision texture experiment

The dependency-free texture diagnostic measures neighboring-pixel absolute-difference energy in two *registered*, equally sized normalized grayscale face crops. It flags strong smoothing or added high-frequency detail and fails closed for flat originals. The default 35% tolerance is provisional and uncalibrated.

This is not a skin-authenticity classifier or identity verifier: grain, scratches, sharpening and alignment can change the score. Use with geometry, independently validated reference similarity, visual review, and explicit owner approval. No pretrained model or commercial dependency is installed.
