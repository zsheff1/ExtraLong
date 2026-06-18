### This script identifies which scans need to be manually checked.
###
### Ellyn Butler
### October 22, 2020

library(ggplot2) #V 3.3.2
library(ggpubr) #V 0.4.0
library(pROC) #V 1.16.2

manual_df <- read.csv('~/Documents/ExtraLong/data/qualityAssessment/rawManualRatings.csv')
quality_df <- read.csv('~/Documents/ExtraLong/data/freesurferCrossSectional/tabulated/quality_2020-11-09.csv')

quality_df <- quality_df[!is.na(quality_df$holes_total), ]
# November 9, 2020: Get rid of sub-98585_ses-PNC1 because didn't fully get
# through freesurfer after multiple tries, and the image quality is really bad
# (by visual inspection by me and someone else in the past), so I just gave up
quality_df$holes_rh <- as.numeric(as.character(quality_df$holes_rh))
quality_df$euler_rh <- as.numeric(as.character(quality_df$euler_lh))


final_df <- merge(manual_df, quality_df, all=TRUE)

# Check values for three sessions whose fmriprep output went missing
final_df[final_df$bblid == 100278 & final_df$seslabel == 'PNC3', ] # EXCLUDE!
final_df[final_df$bblid == 117595 & final_df$seslabel == 'PNC1', ] # Do not exclude, and also PS_PS
final_df[final_df$bblid == 98585 & final_df$seslabel == 'PNC1', ] # EXCLUDE!

# Create plot of distributions of quality metrics
for (qualmet in names(quality_df)[3:12]) {
  qual_plot <- ggplot(quality_df, aes_string(x=qualmet)) + theme_linedraw() +
    geom_histogram(bins=50)
  assign(paste0(qualmet, '_plot'), qual_plot)
}

pdf(file='~/Documents/ExtraLong/plots/qualityMetrics.pdf', width=12, height=3.5)
ggarrange(cnr_graycsf_lh_plot, cnr_graycsf_rh_plot, cnr_graywhite_lh_plot, cnr_graywhite_rh_plot, ncol=4)
ggarrange(holes_lh_plot, holes_rh_plot, holes_total_plot, ncol=3)
ggarrange(euler_lh_plot, euler_rh_plot, euler_total_plot, ncol=3)
dev.off()

# Plot holes and cnr, colored by previously conducted manual exclusions
final_df2 <- merge(manual_df, quality_df)
man_plot <- ggplot(final_df2, aes(x=holes_total, y=cnr_graycsf_lh, color=rawT1Exclude)) +
  theme_linedraw() + geom_point() + theme(legend.position='bottom')

# Receiver Operating Curve
roc_info <- roc(rawT1Exclude ~ holes_total + cnr_graycsf_lh, data=final_df2)
roc_plot <- ggroc(roc_info) + theme_linedraw() + theme(legend.position='bottom')

pdf(file='~/Documents/ExtraLong/plots/corROC.pdf', width=10, height=5)
ggarrange(man_plot, roc_plot, ncol=2)
dev.off()

# AUC
roc_info$holes_total
roc_info$cnr_graycsf_lh

# Based on inspection of the plots, the following cutoff was selected:
# Holes >= 120
# Given the low AUC for CNR, only number of holes will be utilized

max(roc_info$holes_total$thresholds[which(roc_info$holes_total$sensitivities > 0.95)])

min(roc_info$holes_total$sensitivities[which(roc_info$holes_total$sensitivities > 0.95)])
max(roc_info$holes_total$specificities[which(roc_info$holes_total$sensitivities > 0.95)])


# Export bblids and seslabels for scans that need to be manually reviewed
manual_df$bblid_seslabel <- paste(manual_df$bblid, manual_df$seslabel, sep='_')
quality_df$bblid_seslabel <- paste(quality_df$bblid, quality_df$seslabel, sep='_')
rev_df <- quality_df[!(quality_df$bblid_seslabel %in% manual_df$bblid_seslabel) &
  quality_df$holes_total >= 120, c('bblid', 'seslabel')]

rev_df$rating <- ''

write.csv(rev_df, file='~/Documents/ExtraLong/data/qualityAssessment/rawManualRatings_ERB2.csv', row.names=FALSE)


















#
