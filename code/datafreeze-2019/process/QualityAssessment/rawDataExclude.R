### This script merges the hand QA that has been performed for a few studies
### together with all of the subject identifiers to figure out how many scans
### have not been manually reviewed.
###
### Ellyn Butler
### October 15, 2020


grmpy <- read.csv('~/Documents/ExtraLong/data/qualityAssessment/n231_GRMPY_manualQA_20200728_needsSCANID.csv')
#reward <- read.csv('~/Documents/ExtraLong/data/qualityAssessment/n489_reward_QAFlags_Structural_final.csv')
pnc <- read.csv('~/Documents/ExtraLong/data/qualityAssessment/n2416_t1QaData_20170516.csv')
extralong <- read.csv('~/Documents/ExtraLong/data/demographicsClinical/scanid_to_seslabel_demo_20200531.csv')

# grmpy: rating
# reward: (only done manually after flagging)
# pnc: averageManualRating

grmpy <- grmpy[, c('bblid', 'scanid', 'rating')]
pnc <- pnc[, c('bblid', 'scanid', 'averageManualRating')]
names(pnc) <- c('bblid', 'scanid', 'rating')

qa_df <- rbind(grmpy, pnc)
qa_df <- merge(qa_df, extralong)

qa_df$rawT1Exclude <- ifelse(qa_df$rating < 1, TRUE, FALSE)
qa_df <- qa_df[, c('bblid', 'scanid', 'seslabel', 'rawT1Exclude')]

###### CHANGE rawT1Exclude for clearly bad images identified by chance ######
qa_df[qa_df$bblid == 117595 & qa_df$seslabel == 'PNC1', 'rawT1Exclude'] <- TRUE
# ^ rating was 1.667... WHY SO HIGH???

write.csv(qa_df, '~/Documents/ExtraLong/data/qualityAssessment/rawManualRatings.csv', row.names=FALSE)
