### After running inspectQCDistns.R, this script was run to second
### guess the exclusion criteria decided by previous manual raters, with the
### discovery that sub-100278 ses-PNC3 is actually a really crappy image. All
### images with more than 250 holes that were not previously excluded were viewed
### to determine if they should remain in the final sample. After this,
### sessionsForANTsSST.R was run.
###
### Ellyn Butler
### November 11, 2020

exclude_df <- read.csv('~/Documents/ExtraLong/data/qualityAssessment/rawManualRatings.csv')
quality_df <- read.csv('~/Documents/ExtraLong/data/freesurferCrossSectional/tabulated/quality_2020-11-09.csv')

exclude_df <- merge(exclude_df, quality_df)
exclude_df <- exclude_df[!is.na(exclude_df$holes_total), ]
excludeTrunc_df <- exclude_df[exclude_df$holes_total <= 250, ]
excludeRev_df <- exclude_df[exclude_df$holes_total > 250, ] # OOPS: SHOULD HAVE ONLY BEEN ONES THAT WERE PREVIOUSlY INCLUDED... looked at too many images

excludeTrunc_df <- excludeTrunc_df[, c('bblid', 'seslabel', 'rawT1Exclude')]
write.csv(excludeTrunc_df, file='~/Documents/ExtraLong/data/qualityAssessment/rawManualRatings_trunc.csv', row.names=FALSE)

excludeRev_df <- excludeRev_df[, c('bblid', 'seslabel')]
excludeRev_df$rating <- ''
excludeRev_df$notes <- ''
write.csv(excludeRev_df, file='~/Documents/ExtraLong/data/qualityAssessment/rawManualRatings_revised2.csv', row.names=FALSE)
