### This script plots age for each visit, colored by unique combinations
### of scanning parameters (total visits = 2332) (average num visits = 3.37)
###
### Ellyn Butler
### June 3, 2020 - June 4, 2020

library('ggplot2')
library('ggpubr')
library('dplyr')

params_df <- read.csv('~/Documents/ExtraLong/data/acquisitionInfo/parameters.csv')


######## Get rid of unique scans
params_df$bblid_seslabel <- paste(params_df$bblid, params_df$seslabel, sep="_")
params_df <- params_df[!(params_df$bblid_seslabel %in% c("112061_SYRP1",
  "130896_AGGY1", "19800_NEFF1", "19830_NEFF1", "110177_PNC2")),]
row.names(params_df) <- 1:nrow(params_df)
checkalone <- table(params_df$bblid)[table(params_df$bblid) == 1]
params_df <- params_df[!(params_df$bblid %in% names(checkalone)),]
row.names(params_df) <- 1:nrow(params_df)

params_df$Scanner_Te_Tr_Flip <- paste(params_df$ManufacturersModelName,
  params_df$EchoTime, params_df$RepetitionTime, params_df$FlipAngle, sep="_")


######## Merge data
demo_df <- read.csv('~/Documents/ExtraLong/data/demographicsClinical/scanid_to_seslabel_demo_20200531.csv')
diag_df <- read.csv('~/Documents/ExtraLong/data/demographicsClinical/diagnosis_long_final.csv')

full_df <- merge(params_df, demo_df)
full_df <- merge(full_df, demo_df)

sortedBBLID <- full_df %>% group_by(bblid) %>% summarise(m=min(scanage_years)) %>% arrange(m)
sortedBBLID$row <- as.numeric(rownames(sortedBBLID))
newDataTable <- full_df %>% left_join(sortedBBLID%>%select(bblid,row),by="bblid")
sortedBBLID$bblid <- factor(sortedBBLID$bblid)
newDataTable$sex <- recode(newDataTable$sex, `2`="Female", `1`="Male")
newDataTable$sex <- ordered(newDataTable$sex, c("Male","Female"))
newDataTable$race <- recode(newDataTable$race, "1"="White", "2"="Black", "3"="Native",
  "4"="Asian", "5"="Multi", "6"="Hawaiian", "9"="Other", .missing="Unknown")
newDataTable$race <- ordered(newDataTable$race, c("White", "Native",
  "Asian", "Multi", "Other", "Unknown", "Black"))
newDataTable$Scanner_Te_Tr_Flip <- ordered(newDataTable$Scanner_Te_Tr_Flip,
  c("Prisma_0.00345_1.81_9", "Prisma_fit_0.0029_2.5_8", "TrioTim_0.00351_1.81_9",
  "TrioTim_0.004_1.85_9"))
newDataTable$study <- ordered(newDataTable$study, c("PNC_CS_810336", "PNC_LG_810336",
  "AGGY_808689", "ONM_816275", "CONTE_815814", "GRMPY_822831",
  "FNDM1_810211", "FNDM2_810211", "NEFF_818028", "NODRA_816281", "DAY2_808799",
  "SYRP_818621", "MOTIVE"))
newDataTable$study <- recode(newDataTable$study, "PNC_CS_810336"="PNC_CS",
  "PNC_LG_810336"="PNC_LG", "AGGY_808689"="AGGY", "ONM_816275"="ONM",
  "CONTE_815814"="CONTE", "GRMPY_822831"="GRMPY", "FNDM1_810211"="FNDM",
  "FNDM2_810211"="FNDM", "NEFF_818028"="NEFF", "NODRA_816281"="NODRA",
  "DAY2_808799"="DAY2", "SYRP_818621"="SYRP")

######## Plot
first_df <- newDataTable[match(unique(newDataTable$bblid), newDataTable$bblid),]

sex_subtit <- paste0("N Female=", nrow(first_df[first_df$sex == "Female",]),
  ", N Male=", nrow(first_df[first_df$sex == "Male",]))
sex_fig <- ggplot(data = newDataTable, aes(x=reorder(row,scanage_years,FUN = min),
    y=scanage_years,color=sex)) + theme_linedraw() +
  geom_point(size = .5, alpha = .5) + geom_line(alpha = .5) +
  scale_x_discrete(breaks = seq(1, length(sortedBBLID$bblid), 50)) +
  coord_flip(clip = "off") +
  scale_color_manual(values = c("purple4","palegreen3"), labels=c("Male","Female"))+
  labs(title = "Sex of Longitudinal Participants", subtitle = sex_subtit,
    y = "Age (years)", x = "Participant") +
  theme(legend.position = c(.8,.2))

race_subtit <- paste0("N White=", nrow(first_df[first_df$race == "White",]),
  ", N Native=", nrow(first_df[first_df$race == "Native",]),
  ", N Asian=", nrow(first_df[first_df$race == "Asian",]),
  ", N Multi=", nrow(first_df[first_df$race == "Multi",]),
  ", N Other=", nrow(first_df[first_df$race == "Other",]),
  ", N Unknown=", nrow(first_df[first_df$race == "Unknown",]),
  ", N Black=", nrow(first_df[first_df$race == "Black",]))
race_fig <- ggplot(data = newDataTable, aes(x=reorder(row,scanage_years,FUN = min),
    y=scanage_years,color=race)) + theme_linedraw() +
  geom_point(size = .5, alpha = .5) + geom_line(alpha = .8) +
  scale_x_discrete(breaks = seq(1, length(sortedBBLID$bblid), 50)) +
  coord_flip(clip = "off") +
  scale_color_manual(values = c("blue1", "slateblue1", "turquoise",
    "lightskyblue2", "plum2", "orange", "red"), labels=c("White", "Native",
    "Asian", "Multi", "Other", "Unknown", "Black"))+
  labs(title = "Race of Longitudinal Participants", subtitle = race_subtit,
    y = "Age (years)", x = "Participant") +
  theme(legend.position = c(.8,.2))

diagnosis_fig #TBD

param_subtit <- paste0("Prisma_0.00345_1.81_9 = ",
  nrow(newDataTable[newDataTable$Scanner_Te_Tr_Flip == "Prisma_0.00345_1.81_9",]),
  ", Prisma_fit_0.0029_2.5_8 = ",
  nrow(newDataTable[newDataTable$Scanner_Te_Tr_Flip == "Prisma_fit_0.0029_2.5_8",]),
  ", \nTrioTim_0.00351_1.81_9 = ",
  nrow(newDataTable[newDataTable$Scanner_Te_Tr_Flip == "TrioTim_0.00351_1.81_9",]),
  ", TrioTim_0.004_1.85_9 = ",
   nrow(newDataTable[newDataTable$Scanner_Te_Tr_Flip == "TrioTim_0.004_1.85_9",]))
param_fig <- ggplot(data = newDataTable, aes(x=reorder(row, scanage_years, FUN = min),
    y=scanage_years, color=Scanner_Te_Tr_Flip)) + theme_linedraw() +
  geom_point(size = .5, alpha = .5) + geom_line(alpha = .8) +
  scale_x_discrete(breaks = seq(1, length(sortedBBLID$bblid), 50)) +
  coord_flip(clip = "off") +
  scale_color_manual(values = c("black", "red", "blue", "green"),
    labels=c("Prisma_0.00345_1.81_9", "Prisma_fit_0.0029_2.5_8", "TrioTim_0.00351_1.81_9",
  "TrioTim_0.004_1.85_9"))+
  labs(title = "Parameters", subtitle = param_subtit,
    y = "Age (years)", x = "Participant") +
  theme(legend.position = c(.8,.2))

study_subtit <- ""
levels <- levels(newDataTable$study)
for (i in 1:length(levels)) {
  if (i < length(levels)) {
    if (i %% 4 != 0) {
      study_subtit <- paste0(study_subtit, levels[i], " = ",
        nrow(newDataTable[newDataTable$study == levels[i], ]), ", ")
    } else {
      study_subtit <- paste0(study_subtit, levels[i], " = ",
        nrow(newDataTable[newDataTable$study == levels[i], ]), ",\n")
    }
  } else {
    study_subtit <- paste0(study_subtit, levels[i], " = ",
      nrow(newDataTable[newDataTable$study == levels[i], ]))
  }
}
study_fig <- ggplot(data = newDataTable, aes(x=reorder(row, scanage_years, FUN = min),
    y=scanage_years, color=study)) + theme_linedraw() +
  geom_point(size = .5, alpha = .5) + geom_line(alpha = .8) +
  scale_x_discrete(breaks = seq(1, length(sortedBBLID$bblid), 50)) +
  coord_flip(clip = "off") +
  labs(title = "Studies", subtitle = study_subtit,
    y = "Age (years)", x = "Participant") +
  theme(legend.position = c(.8,.4))

pdf(file="~/Documents/ExtraLong/plots/age_by_important_factors.pdf", width=14, height=14)
ggarrange(sex_fig, race_fig, param_fig, study_fig, nrow=2, ncol=2,
          labels=c("A", "B", "C", "D"))
dev.off()


# Unique scans:
# 1) bblid 112061, SYRP1
# 2) bblid 130896, AGGY1
# 3) bblid 19800, NEFF1
# 4) bblid 19830, NEFF1
# 5) bblid 110177, PNC2
