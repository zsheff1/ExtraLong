### This script determines which sessions should go through antssst
###
### Ellyn Butler
### October 23, 2020 - November 10, 2020

quality_df <- read.csv('~/Documents/ExtraLong/data/freesurferCrossSectional/tabulated/quality_2020-11-09.csv')
excludeTrunc_df <- read.csv('~/Documents/ExtraLong/data/qualityAssessment/rawManualRatings_trunc.csv')
excludeRev_df <- read.csv('~/Documents/ExtraLong/data/qualityAssessment/rawManualRatings_revised.csv')
excludeMore_df <- read.csv('~/Documents/ExtraLong/data/qualityAssessment/rawManualRatings_ERB.csv')

quality_df <- quality_df[, c('bblid', 'seslabel')]

excludeRev_df$rawT1Exclude <- ifelse(excludeRev_df$rating < 1, TRUE, FALSE)
excludeMore_df$rawT1Exclude <- ifelse(excludeMore_df$rating < 1, TRUE, FALSE)

excludeRev_df <- excludeRev_df[, c('bblid', 'seslabel', 'rawT1Exclude')]
excludeTrunc_df <- excludeTrunc_df[, c('bblid', 'seslabel', 'rawT1Exclude')]

# Get the number of 0s, 1s and 2s in excludeMore_df for wiki
nrow(excludeMore_df[excludeMore_df$rating == 0, ])
nrow(excludeMore_df[excludeMore_df$rating == 1, ])
nrow(excludeMore_df[excludeMore_df$rating == 2, ])

excludeMore_df <- excludeMore_df[, c('bblid', 'seslabel', 'rawT1Exclude')]

exclude_df2 <- merge(excludeMore_df, excludeTrunc_df, all=TRUE)
exclude_df2 <- merge(exclude_df2, excludeRev_df, all=TRUE)
quality_df2 <- merge(quality_df, exclude_df2, all=TRUE)


# If NA, that means they had very few holes, and as such did not require manual review,
# so change NA to FALSE

quality_df2[is.na(quality_df2$rawT1Exclude), 'rawT1Exclude'] <- FALSE

# For all bblids that don't have at least 2 sessions that passed manual QA,
# exclude the remaining image

finalExclude <- function(i) {
  bblid <- quality_df2[i, 'bblid']
  sessions <- quality_df2[quality_df2$bblid == bblid & quality_df2$rawT1Exclude == FALSE, 'seslabel']
  if (length(sessions) < 2 | quality_df2[i, 'rawT1Exclude'] == TRUE) { TRUE } else { FALSE }
}

quality_df2$antssstExclude <- sapply(1:nrow(quality_df2), finalExclude) # 64 excluded in total

# Get the number excluded based on very poor quality
sum(quality_df2$rawT1Exclude)

# Get the number excluded based on being a singleton
sum(quality_df2$antssstExclude) - sum(quality_df2$rawT1Exclude)

quality_df2 <- quality_df2[, c('bblid', 'seslabel', 'antssstExclude')]

write.csv(quality_df2, file='~/Documents/ExtraLong/data/qualityAssessment/antssstExclude.csv', row.names=FALSE)
