
# Read in all the necessary data and packages, while doing some light formatting so that session and subject ID variables match across data sets.
library(tidyverse)
library(VIM)
library(ggrepel)
library(gridExtra)
library(readr)
library(kableExtra)
library(mosaic)
library(gtsummary)
library(ggpubr)

asegLong.df <- read_delim("/project/ExtraLong/data/freesurferLongitudinal/qdec/freesurferLongitudinal_aseg.table.txt",
    delim = "\t", escape_double = FALSE,
    trim_ws = TRUE)
asegCross.df <- read.delim("/project/ExtraLong/data/freesurferCrossSectional/tabulated/freesurferCrossSectional_aseg.table.txt")
ScanTime.df <- read_table2("/project/ExtraLong/data/freesurferLongitudinal/qdec/qdec_table.dat")
Exclude.df <- read_csv("/project/ExtraLong/data/qualityAssessment/antssstExclude.csv") %>%
  rename(Subject.ID = bblid,Session = seslabel) %>%
  mutate(Subject.ID = as.character(Subject.ID)) %>%
  mutate(Session = paste("ses-",Session,sep = ""))
QC.long <- read_table("/project/ExtraLong/data/qualityAssessment/AllSessions_quality.csv") %>%
  filter(if_all(.fns = ~ !is.na(.)))
QC.template <- read_csv("/project/ExtraLong/data/freeqcLongitudinal/tabulated/quality_2021-05-20.csv") %>%
   filter(if_all(.fns = ~ !is.na(.)))
demo <- read_csv("/project/bbl_data/longitudinal/demographic/scanid_to_seslabel_demo_20200531.csv")
demo.dict <- read_delim("/project/deid_bblrepo1/n1601_dataFreeze/demographics/demographics_dictionary_20161212.txt",
                        delim = "\t", escape_double = FALSE,
                        trim_ws = TRUE)


# Make holes and euler number numeric variables
QC.template <- QC.template %>%
  mutate(holes_lh = as.numeric(holes_lh),holes_rh = as.numeric(holes_rh),euler_lh = as.numeric(euler_lh),euler_rh = as.numeric(euler_rh))

# Fix Scan data variable
QC.long <- QC.long %>%
  mutate(Scan.Date = str_remove(Scan.Date,pattern = "T.*")) %>%
  mutate(Scan.Date = str_remove(Scan.Date,pattern = '"')) %>%
  mutate(Scan.Date = as.Date(Scan.Date)) %>%
  rename(Subject.ID = fsid)

#Use demo.dict to assign names to the numeric sex, race, and ethnicity variables

demo <- demo %>%
  mutate(sex = case_when(sex == 1 ~ "Male",sex == 2 ~ "Female")) %>%
  mutate(race = case_when(race == 1 ~ "White",race == 2 ~ "Black",race == 3 ~ "Native American",race == 4 ~ "Asian",race == 5 ~ "More than one race",race == 6 ~ "Hawaiian/Pacific",race == 9 ~ "Unknown")) %>%
  mutate(ethnic = case_when(ethnic == 1 ~ "Hispanic/Latino",ethnic == 2 ~ "Not Hispanic/Latino",ethnic == 9 ~ "Unknown")) %>%
  rename(ethnicity = ethnic) %>%
  relocate(bblid,sex,race,ethnicity,seslabel) %>%
  rename(Subject.ID = bblid,Session = seslabel) %>%
  mutate(Session = paste("ses-",Session,sep = ""))

# For four individuals (13473,17491,17940,and 18093) there are discrepancies between the demo and QC.long files with session information. It appears that the session ses-CONTE2 was mislabeled in all four individuals (labeled ses-CONTE1 instead of ses-CONTE2). The following code demonstrates that mistake and fixes it.

MislabeledSubjects <- demo %>%
  group_by(Subject.ID,Session) %>%
  summarize(n = n()) %>%
  filter(n > 1) %>%
  ungroup() %>%
  pull(Subject.ID)

# Compare the session variables in both data frames to see the problem
demo %>%
  filter(Subject.ID %in% MislabeledSubjects) %>%
  filter(str_detect(Session,pattern = "ses-CONTE")) %>%
  select(Subject.ID,sex,race,ethnicity,Session,scanage_years)
QC.long %>%
  filter(Subject.ID %in% MislabeledSubjects) %>%
  filter(str_detect(Session,pattern = "ses-CONTE")) %>%
  select(Subject.ID:Scan.Date)

correctSessionLabel <- function(df){
  subjID <- df %>%
    slice(1) %>%
    pull(Subject.ID)
  if(subjID %in% MislabeledSubjects){
    mislabeledSession <- df %>%
      filter(Session == "ses-CONTE1") %>%
      arrange(timepoint) %>%
      mutate(Session = ifelse(timepoint == max(timepoint),"ses-CONTE2","ses-CONTE1"))

    other.df <- df %>%
      filter(Session != "ses-CONTE1")

    df <- rbind(mislabeledSession,other.df)
  }
  return(df)
}

demo.ID <- demo %>%
  group_split(Subject.ID)
demo <- map_dfr(demo.ID,correctSessionLabel)

QC.long <- QC.long %>%
  left_join(demo)

# Create plots for QC values in QC.template

# Creates vector of column names (QC.measures) that will be used as response variables for each plot, and then maps a function (getQCplot) which creates a quality control plot for each element in that vector.
QC.measures <- QC.template %>%
  select(-bblid,-seslabel) %>%
  colnames()

names.df <- data.frame(Short.Name = c("cnr_graycsf_lh","cnr_graycsf_rh","cnr_graywhite_lh","cnr_graywhite_rh","holes_lh","holes_rh","holes_total","euler_lh","euler_rh","euler_total"),Long.Name = c("CNR Gray-CSF Left Hemisphere", "CNR Gray-CSF Right Hemisphere", "CNR Gray-White Left Hemisphere", "CNR Gray-White Right Hemisphere","Holes Left Hemisphere","Holes Right Hemisphere","Holes Total","Euler Left Hemisphere","Euler Right Hemisphere","Euler Total"))

getQCplot <- function(Measure.of.Interest){

  #if we are plotting the number of holes in an image, we want to highlight extreme high values, not low values
  if(str_detect(Measure.of.Interest,pattern = "holes")){

    Name.of.Measure <- names.df %>%
      filter(Short.Name == Measure.of.Interest) %>%
      pull(Long.Name)

    Measure.of.Interest <- quo(!!sym(Measure.of.Interest))

    QC.template.label <- QC.template %>%
      mutate(Z.score = (!!Measure.of.Interest - mean(!!Measure.of.Interest))/sd(!!Measure.of.Interest)) %>%
      filter(Z.score > 2)

    QC.template.bblid <- QC.template %>%
      mutate(Z.score = scale(!!Measure.of.Interest)) %>%
      filter(Z.score > 2) %>%
      pull(bblid)

    Summary.df <- QC.template %>%
      summarize(Mean = mean(!!Measure.of.Interest),SD = sd(!!Measure.of.Interest))

    Mean <- Summary.df$Mean
    SD <- Summary.df$SD

    QC.template %>%
      mutate(LowQuality = ifelse(bblid %in% QC.template.bblid,"Z-Score > 2","Z-Score < 2")) %>%
      ggplot(aes(x = !!Measure.of.Interest,y = as.factor(bblid))) + geom_point(aes(color = LowQuality)) + scale_y_discrete(breaks = NULL,expand = expansion(add = 15)) + theme(axis.text.y = element_blank(),axis.ticks.y = element_blank(),panel.grid.major = element_blank(),panel.grid.minor = element_blank(),panel.background = element_blank(),axis.line = element_line(color = "black"),plot.caption = element_text(hjust = 0,size = 6)) + labs(y = "ID #",x = paste(Name.of.Measure)) + scale_color_brewer(name = "Low Quality Templates",palette = "Dark2") + geom_vline(xintercept = Mean) + geom_vline(xintercept = (Mean - 2*SD),lty = 2) + geom_vline(xintercept = (Mean + 2*SD),lty = 2) + geom_label_repel(data = QC.template.label,aes(label=bblid),max.overlaps = getOption("ggrepel.max.overlaps", default = Inf))
  } else{

    Name.of.Measure <- names.df %>%
      filter(Short.Name == !!Measure.of.Interest) %>%
      pull(Long.Name)

    Measure.of.Interest <- quo(!!sym(Measure.of.Interest))

    QC.template.label <- QC.template %>%
      mutate(Z.score = (!!Measure.of.Interest-mean(!!Measure.of.Interest))/sd(!!Measure.of.Interest)) %>%
      filter(Z.score < -2)

    QC.template.bblid <- QC.template %>%
      mutate(Z.score = scale(!!Measure.of.Interest)) %>%
      filter(Z.score < -2) %>%
      pull(bblid)

    Summary.df <- QC.template %>%
      summarize(Mean = mean(!!Measure.of.Interest),SD = sd(!!Measure.of.Interest))

    Mean <- Summary.df$Mean
    SD <- Summary.df$SD

    QC.template %>%
      mutate(LowQuality = ifelse(bblid %in% QC.template.bblid,"Z-Score < -2","Z-Score > -2")) %>%
      ggplot(aes(x = !!Measure.of.Interest,y = as.factor(bblid))) + geom_point(aes(color = LowQuality)) + scale_y_discrete(breaks = NULL,expand = expansion(add = 15)) + theme(axis.text.y = element_blank(),axis.ticks.y = element_blank(),panel.grid.major = element_blank(),panel.grid.minor = element_blank(),panel.background = element_blank(),axis.line = element_line(color = "black"),plot.caption = element_text(hjust = 0,size = 6)) + labs(y = "ID #",x = paste(Name.of.Measure)) + scale_color_brewer(name = "Low Quality Templates",palette = "Dark2") + geom_vline(xintercept = Mean) + geom_vline(xintercept = (Mean - 2*SD),lty = 2) + geom_vline(xintercept = (Mean + 2*SD),lty = 2)  + geom_label_repel(data = QC.template.label,aes(label=bblid),max.overlaps = getOption("ggrepel.max.overlaps", default = Inf))
  }
}

QCplots <- map(QC.measures,getQCplot)

# I commented out the plots for holes since they are perfectly correlated with the euler number plots
QCplots[[1]]
QCplots[[2]]
QCplots[[3]]
QCplots[[4]]
#QCplots[[5]]
#QCplots[[6]]
#QCplots[[7]]
QCplots[[8]]
QCplots[[9]]
QCplots[[10]]

### CNR Gray-CSF right hemisphere vs. CNR left hemisphere

QC.template %>%
  ggplot(aes(x = cnr_graycsf_lh,y = cnr_graycsf_rh)) + geom_point(color = "lightslateblue") + geom_smooth(color = "lightslateblue") + theme_classic() + labs(x = "CNR Gray-CSF Left Hemisphere",y = "CNR Gray-CSF Right Hemisphere")

### CNR Gray-White right hemisphere vs. CNR left hemisphere

QC.template %>%
  ggplot(aes(x = cnr_graywhite_lh,y = cnr_graywhite_rh)) + geom_point(color = "lightslateblue") + geom_smooth(color = "lightslateblue") + theme_classic() + labs(x = "CNR Gray-White Left Hemisphere",y = "CNR Gray-White Right Hemisphere")

## Flagging subjects with bad QC values on a variety of measures

QC.NumTimepoints <- demo %>%
  distinct(Subject.ID,.keep_all = TRUE) %>%
  select(Subject.ID,num_timepoints)
QC.timepoint <- demo %>%
  group_by(Subject.ID) %>%
  arrange(timepoint) %>%
  mutate(Avg.time.between.scans = mean(diff(scanage_years))) %>%
  mutate(Max.time.between.scans = max(diff(scanage_years))) %>%
  mutate(Age.at.scans = str_c(scanage_years,sep = "",collapse = ", ")) %>%
  ungroup() %>%
  relocate(Subject.ID:Session,Age.at.scans,Avg.time.between.scans,Max.time.between.scans) %>%
  select(Subject.ID,Age.at.scans,Avg.time.between.scans,Max.time.between.scans) %>%
  distinct() %>%
  left_join(QC.NumTimepoints)

# Calculates Z-scores for each quality control measure, sums number of Z-scores < -2 for each subject, and outputs these findings as a html table. I don't include holes # in the analysis since euler # is a direct function of it (euler= 2 - 2*# of holes).
QC.template %>%
  select(-holes_lh,-holes_rh,-holes_total,-seslabel) %>%
  pivot_longer(cols = cnr_graycsf_lh:euler_total,names_to = "QC.measure",values_to = "QC.value") %>%
  group_by(QC.measure) %>%
  mutate(Z.score = as.vector(scale(QC.value))) %>%
  mutate(Poor.Quality = ifelse(Z.score < -2,1,0)) %>%
  ungroup() %>%
  group_by(bblid) %>%
  mutate(PoorQuality.Total = sum(Poor.Quality)) %>%
  ungroup() %>%
  select(-QC.value,-Poor.Quality) %>%
  pivot_wider(names_from = QC.measure,values_from = Z.score,names_glue = "Z-score:<br/>{QC.measure}") %>%
  arrange(desc(PoorQuality.Total)) %>%
  filter(PoorQuality.Total >= 1) %>%
  left_join(QC.timepoint,by = c("bblid" = "Subject.ID")) %>%
  select(-Avg.time.between.scans,-Max.time.between.scans) %>%
  rename("Number of timepoints" = num_timepoints,"Age at scan" = Age.at.scans) %>%
  mutate(across(`Z-score:<br/>cnr_graycsf_lh`:`Z-score:<br/>euler_total`,~ cell_spec(.x,format = "html",color = ifelse(.x < -2,"red","black")))) %>%
  rename("Poor QC Measures <br/> (# total)" = PoorQuality.Total) %>%
  kbl(escape = F,format = "html") %>%
  kable_minimal()

### QC template by age, number of timepoints, max time between timepoints, and average time between timepoints

QC.template %>%
  select(-(holes_lh:holes_total)) %>%
  left_join(QC.timepoint,by = c("bblid" = "Subject.ID")) %>%
  pivot_longer(cols = cnr_graycsf_lh:euler_total,names_to = "QC.measures",values_to = "QC.values") %>%
  group_by(QC.measures) %>%
  mutate(QC.values.scaled = as.numeric(scale(QC.values))) %>%
  ungroup() %>%
  mutate(Quality = ifelse(QC.values.scaled < -2,"Poor (Z-score < -2)","Adequate (Z-score > -2)")) %>%
  filter(!(QC.measures %in% c("cnr_graycsf_lh","cnr_graycsf_rh"))) %>%
  ggplot(aes(x = Max.time.between.scans,color = Quality,fill = Quality)) + geom_density(alpha = .1) + scale_color_brewer(palette = "Accent") + scale_fill_brewer(palette = "Accent") + facet_wrap(~QC.measures) + labs(x = "Max time between scans (years)") + theme_minimal() + labs(fill = "Template Quality",color = "Template Quality")


QC.template %>%
  select(-(holes_lh:holes_total)) %>%
  left_join(QC.timepoint,by = c("bblid" = "Subject.ID")) %>%
  pivot_longer(cols = cnr_graycsf_lh:euler_total,names_to = "QC.measures",values_to = "QC.values") %>%
  group_by(QC.measures) %>%
  mutate(QC.values.scaled = as.numeric(scale(QC.values))) %>%
  mutate(Quality = ifelse(QC.values.scaled < -2,"Poor (Z-score < -2)","Adequate (Z-score > -2)")) %>%
  filter(!(QC.measures %in% c("cnr_graycsf_lh","cnr_graycsf_rh"))) %>%
  ggplot(aes(x = Avg.time.between.scans,color = Quality,fill = Quality)) + geom_density(alpha = .1) + scale_color_brewer(palette = "Accent") + scale_fill_brewer(palette = "Accent") + facet_wrap(~QC.measures) + labs(x = "Average time between scans (years)") + theme_minimal() + labs(fill = "Template Quality",color = "Template Quality")

QC.template %>%
  select(-(holes_lh:holes_total)) %>%
  left_join(QC.timepoint,by = c("bblid" = "Subject.ID")) %>%
  pivot_longer(cols = cnr_graycsf_lh:euler_total,names_to = "QC.measures",values_to = "QC.values") %>%
  group_by(QC.measures) %>%
  mutate(QC.values.scaled = as.numeric(scale(QC.values))) %>%
  mutate(Quality = ifelse(QC.values.scaled < -2,"Poor (Z-score < -2)","Adequate (Z-score > -2)")) %>%
  filter(!(QC.measures %in% c("cnr_graycsf_lh","cnr_graycsf_rh"))) %>%
  group_by(QC.measures,Quality) %>%
  summarize(Mean.Timepoints = mean(num_timepoints),SD.Timepoints = sd(num_timepoints)) %>%
  mutate(Quality = factor(Quality,levels = c("Poor (Z-score < -2)","Adequate (Z-score > -2)"))) %>%
  ggplot(aes(x = Quality,y = Mean.Timepoints,color = Quality,fill = Quality)) + geom_bar(stat = "identity",alpha = .5) + geom_errorbar(aes(ymin = Mean.Timepoints - SD.Timepoints,ymax = Mean.Timepoints + SD.Timepoints)) + facet_wrap(~QC.measures) + labs(x = "Template Quality",y = "Number of Timepoints (Mean +- SD)",fill = "Template Quality",color = "Template Quality") + theme_minimal() + scale_color_brewer(palette = "Accent") + scale_fill_brewer(palette = "Accent")

QC.template %>%
  select(-(holes_lh:holes_total)) %>%
  left_join(QC.timepoint,by = c("bblid" = "Subject.ID")) %>%
  mutate(Age.first.scan = as.numeric(str_remove_all(Age.at.scans,pattern = ",.*"))) %>%
  pivot_longer(cols = cnr_graycsf_lh:euler_total,names_to = "QC.measures",values_to = "QC.values") %>%
  group_by(QC.measures) %>%
  mutate(QC.values.scaled = as.numeric(scale(QC.values))) %>%
  ungroup() %>%
  mutate(Quality = ifelse(QC.values.scaled < -2,"Poor (Z-score < -2)","Adequate (Z-score > -2)")) %>%
  filter(!(QC.measures %in% c("cnr_graycsf_lh","cnr_graycsf_rh"))) %>%
  ggplot(aes(x = Age.first.scan,color = Quality,fill = Quality)) + geom_density(alpha = .1) + scale_color_brewer(palette = "Accent") + scale_fill_brewer(palette = "Accent") + facet_wrap(~QC.measures) + labs(x = "Age at first scan (years)") + theme_minimal() + labs(fill = "Template Quality",color = "Template Quality")

# The following plot examines whether individuals with poor templates have more variability across their scans than individuals with adequate templates.

QC.SD <- QC.long %>%
  group_by(Subject.ID) %>%
  mutate(num_timepoints = n()) %>%
  ungroup() %>%
  filter(num_timepoints > 1) %>%
  select(!contains("holes")) %>%
  pivot_longer(cols = euler_lh:cnr_graywhite_rh,names_to = "QC.measures",values_to = "QC.values") %>%
  group_by(Subject.ID,QC.measures) %>%
  summarize(SD = sd(QC.values)) %>%
  ungroup()

QC.template %>%
  select(!contains("holes")) %>%
  pivot_longer(cols = cnr_graycsf_lh:euler_total,names_to = "QC.measures",values_to = "QC.values") %>%
  rename(Subject.ID = bblid) %>%
  left_join(QC.SD) %>%
  filter(!is.na(SD)) %>%
  group_by(QC.measures) %>%
  mutate(Z.values = as.numeric(scale(QC.values))) %>%
  ungroup() %>%
  mutate(Template.quality = ifelse(Z.values < -2, "Poor (Z-score < -2)","Adequate (Z-score > -2)")) %>%
  filter(!(QC.measures %in% c("cnr_graycsf_lh","cnr_graycsf_rh"))) %>%
  ggplot(aes(x = SD,color = Template.quality,fill = Template.quality)) + geom_density(alpha = .5) + facet_wrap(~QC.measures,scales = "free") + theme_classic() + labs(x = "Quality metric standard deviation (within individual)",fill = "Template Quality",color = "Template Quality") + scale_color_brewer(palette = "Dark2") + scale_fill_brewer(palette = "Dark2")


# Examining aseg values across sessions

# First, we will add in the scan date for each session so we can plot subjects longitudinally.

asegLong.df <- asegLong.df %>%
  rename(id = `Measure:volume`) %>%
  mutate(id = str_remove(id,pattern = "\\.long.Template.*")) %>%
  left_join(ScanTime.df,by = c("id" = "fsid")) %>%
  rename(Scan.Date = `Scan-Date`) %>%
  relocate(id,Scan.Date) %>%
  mutate(Scan.Date = str_remove(Scan.Date,pattern = "T.*")) %>%
  mutate(Scan.Date = str_remove(Scan.Date,pattern = '"')) %>%
  mutate(Scan.Date = as.Date(Scan.Date)) %>%
  separate(id, into = c("Subject.ID","Session"),sep = "/") %>%
  mutate(Subject.ID = str_remove(Subject.ID,pattern = "sub-"))

# At first glance, the estimated total intracranial volume appears not to change across time for any individual.

asegLong.df %>%
  ggplot(aes(x = Scan.Date,y = EstimatedTotalIntraCranialVol,group = Subject.ID)) + geom_point(color = "lightsteelblue") + geom_line(color = "lightsteelblue") + theme_classic() + labs(x = "Scan Date",y = "Estimated Total Intracranial Volume",title = "Intracranial Volume by Subject")

# The following data frame confirms this, as the highest variability of intracranial volume for a particular subject is 0 (i.e across scan dates estimated intracranial volume never changes).

asegLong.df %>%
  group_by(Subject.ID) %>%
  summarize(IntraCranialVolVariance = var(EstimatedTotalIntraCranialVol)) %>%
  arrange(desc(IntraCranialVolVariance)) %>%
  head()

# Upon reading freesurfer documentation, I discovered that freesurfer's longitudinal pipeline assumes total intracranial volume does not change across time and therefore it is initialized from the template. So, I reran the longitudinal eTIV plot with the cross-sectional data.

# Same as before, I start by adding scan date to the cross-sectional data so we can plot subjects over time. Also, I only include individuals who passed the cross-sectional qc inspection as indicated by the antsstExclude dataset.

asegCross.df <- asegCross.df %>%
  rename(id = Measure.volume) %>%
  mutate(id = str_remove(id,pattern = "\\.long.Template.*")) %>%
  left_join(ScanTime.df,by = c("id" = "fsid")) %>%
  rename(Scan.Date = `Scan-Date`) %>%
  relocate(id,Scan.Date) %>%
  mutate(Scan.Date = str_remove(Scan.Date,pattern = "T.*")) %>%
  mutate(Scan.Date = str_remove(Scan.Date,pattern = '"')) %>%
  mutate(Scan.Date = as.Date(Scan.Date)) %>%
  separate(id, into = c("Subject.ID","Session"),sep = "/") %>%
  mutate(Subject.ID = str_remove(Subject.ID,pattern = "sub-")) %>%
  left_join(Exclude.df) %>%
  filter(antssstExclude == FALSE)

#Visualize intracranial volume across time

TIV.byTime <- asegCross.df %>%
  ggplot(aes(x = Scan.Date,y = EstimatedTotalIntraCranialVol,group = Subject.ID)) + geom_point(color = "lightsteelblue") + geom_line(color = "lightsteelblue") + theme_classic() + labs(x = "Scan Date",y = "eTIV",title = "Intracranial Volume by Subject") + geom_smooth(aes(group = 1),color = "black",se = FALSE)

# Function which creates a column that indicates whether a particular subject's eTIV decreases (for all time points) between sessions.

eTIVdecrease <- function(df){
  eTIVs <- df %>%
    arrange(Scan.Date) %>%
    pull(EstimatedTotalIntraCranialVol)
  if(is.unsorted(-eTIVs)){
    df <- df %>%
      mutate(TIVdecrease = "No")
  } else{
    df <- df %>%
      mutate(TIVdecrease = "Yes")
  }

  return(df)
}

# Maps function eTIVdecrease to a list of dataframes where each data frame contains only rows from a particular subject.

asegCross.ID <- asegCross.df %>%
  group_split(Subject.ID)
asegCross.df <- map_dfr(asegCross.ID,eTIVdecrease)

# Plots total intracranial volume over time, grouped by subject ID and whether the total intracranial volume decreased for that subject at every time point.

TIV.split.time <- asegCross.df %>%
    ggplot(aes(x = Scan.Date,y = EstimatedTotalIntraCranialVol,group = Subject.ID)) + geom_point(aes(color = TIVdecrease)) + geom_line(aes(color = TIVdecrease)) + theme(axis.text.x = element_text(size = 6),panel.background = element_blank(),panel.grid.major = element_blank(),panel.grid.minor = element_blank()) + labs(x = "Scan Date",y = "eTIV",title = "Intracranial Volume by Subject") + facet_wrap(~TIVdecrease) + scale_color_brewer(palette = "Dark2") + geom_smooth(aes(group = 1),color = "black",se = FALSE) + labs(color = "TIV decrease across all sessions")

# Function which finds the difference in intracranial volume between a subject's first and last scans.

TIVDiff <- function(df){
  N <- nrow(df)
TIVs <-  df %>%
    arrange(Scan.Date) %>%
    slice(1,N) %>%
    pull(EstimatedTotalIntraCranialVol)
TIVDiff <- TIVs[2] -TIVs[1]
newdf <- data.frame(Subject.ID = df$Subject.ID[1],TIVDiffs = TIVDiff)
return(newdf)
}

TIV_Diff.df <- map_dfr(asegCross.ID,TIVDiff)

# Plots individuals who have significant (Z-score < -2) decreases in intracranial volume

Summary.TIV <- TIV_Diff.df %>%
  summarize(Mean = mean(TIVDiffs),SD = sd(TIVDiffs))

#TIV.Label <- TIV_Diff.df %>%
 # mutate(Z.score = scale(TIVDiffs)) %>%
 # mutate(PoorQuality = ifelse(Z.score < -2,"Poor","Adequate")) %>%
  #filter(PoorQuality == "Poor")

TIV.LastFirst <- TIV_Diff.df %>%
  mutate(Z.score = scale(TIVDiffs)) %>%
  mutate(LargeDiff = ifelse(Z.score < -2,"Z-score < -2","Z-score > -2")) %>%
  ggplot(aes(x = TIVDiffs,y = Subject.ID)) + geom_point(aes(color = LargeDiff)) + theme(axis.text.y = element_blank(),axis.ticks.y = element_blank(),panel.grid.major = element_blank(),panel.grid.minor = element_blank(),panel.background = element_blank(),axis.line = element_line(color = "black")) + geom_vline(data = Summary.TIV,aes(xintercept = Mean)) + geom_vline(data = Summary.TIV,aes(xintercept = Mean + 2*SD),lty = 2) + geom_vline(data = Summary.TIV,aes(xintercept = Mean - 2*SD),lty = 2) + labs(x = "Last Scan TIV - First Scan TIV",y = "Subject ID",color = "TIV difference") + scale_color_brewer(palette = "Dark2") + scale_y_discrete(breaks = NULL,expand = expansion(add = 15)) #+ geom_label_repel(data = TIV.Label,aes(label = Subject.ID))


## Calculating Euler across time

# The following plot looks for whether the euler number has drifted over time.

QC.long %>%
  ggplot(aes(x = Scan.Date,y = euler_total,group = Subject.ID)) + geom_point(color = "lightgray") + geom_path(color = "lightgray") + geom_smooth(aes(group = 1),color = "black") + theme_classic() + labs(x = "Scan date",y = "Euler Total")

QC.long.ID <- QC.long %>%
  group_split(Subject.ID)

# Finds difference in Euler number between last and first scans for a subject
EulerDiff <- function(df){
  N <- nrow(df)
EulerTotals <-  df %>%
    arrange(Scan.Date) %>%
    slice(1,N) %>%
    pull(euler_total)
TotalEulerDiff <- EulerTotals[2] - EulerTotals[1]
df <- data.frame(Subject.ID = df$Subject.ID[1],TotalEulerDiff = TotalEulerDiff)
return(df)
}

# Another plot examining whether the Euler number differs systematically between a subject's first and last scan.

EulerDiff.df <- map_dfr(QC.long.ID,EulerDiff)
Euler.FirstLast <- EulerDiff.df %>%
  ggplot(aes(x = TotalEulerDiff)) + geom_histogram(fill = "lightsteelblue",bins = 75) + theme_classic() + labs(x = "Last scan - first scan (total euler number)")

Template.LowEuler <- QC.template %>%
  mutate(euler_total_Zscore = (euler_total - mean(euler_total))/sd(euler_total)) %>%
  filter(euler_total_Zscore < -2) %>%
  arrange(desc(euler_total_Zscore)) %>%
  pull(bblid)

# The following plot depicts all sessions for each subject whose template euler number has a z-score < -2.

cntr <- 1
QC.long.plot <- list()
for(bblid in Template.LowEuler){
  QC.long.plot[[cntr]] <- QC.long %>%
    mutate(ID = ifelse(Subject.ID == bblid,"Poor Template ID","Adequate Template")) %>%
    mutate(size = ifelse(Subject.ID == bblid,1,.05)) %>%
    mutate(alpha = ifelse(Subject.ID == bblid,1,.1)) %>%
    filter(!(Subject.ID %in% Template.LowEuler) | Subject.ID == bblid) %>%
  ggplot() + geom_point(aes(x = scanage_years,y = euler_total,group = Subject.ID,color = ID,alpha = alpha,size = size)) +  geom_line(aes(x = scanage_years,y = euler_total,group = Subject.ID,color = ID,alpha = alpha)) + scale_alpha_identity() + scale_size_identity() + theme(panel.grid.major = element_blank(),panel.grid.minor = element_blank(),panel.background = element_blank(),axis.line = element_line(color = "black")) + labs(x = "",y = "") + scale_color_brewer(palette = "Dark2")
  cntr <- cntr + 1
}

Euler.poorTemplate <- ggarrange(plotlist = QC.long.plot,common.legend = TRUE,legend = "right",labels = str_c("bblid:",Template.LowEuler,sep = " "),font.label = list(size = 8),label.x = .5)
annotate_figure(Euler.poorTemplate,bottom = text_grob("Age"),left = text_grob("Euler Total",rot = 90))

QC.long.all.plot <- QC.long %>%
    mutate(ID = ifelse(Subject.ID %in% Template.LowEuler,"Poor Template","Adequate Template")) %>%
    mutate(size = ifelse(Subject.ID %in% Template.LowEuler,.25,.25)) %>%
    mutate(alpha = ifelse(Subject.ID %in% Template.LowEuler,1,.25)) %>%
  ggplot() + geom_point(aes(x = scanage_years,y = euler_total,group = Subject.ID,color = ID,alpha = alpha,size = size)) +  geom_line(aes(x = scanage_years,y = euler_total,group = Subject.ID,color = ID,alpha = alpha)) + scale_alpha_identity() + scale_size_identity() + theme(panel.grid.major = element_blank(),panel.grid.minor = element_blank(),panel.background = element_blank(),axis.line = element_line(color = "black")) + labs(x = "",y = "") + scale_color_brewer(palette = "Dark2") #+ geom_smooth(aes(x = scanage_years,y = euler_total,group = ID,color = ID))

### CNR Gray-CSF Left Hemisphere Across Sessions

# Note: the CNR for each individual scan is taken from the LONGITUDINAL images, not the cross-sectional ones like for Euler number.

Template.LowCNR.GrayCSF <- QC.template %>%
  mutate(Z.cnr_graycsf_lh = as.numeric(scale(cnr_graycsf_lh))) %>%
  filter(Z.cnr_graycsf_lh < -2) %>%
  arrange(desc(Z.cnr_graycsf_lh)) %>%
  pull(bblid)

cntr <- 1
CNR_GrayCSF_lh.plot <- list()
for(bblid in Template.LowCNR.GrayCSF){
  CNR_GrayCSF_lh.plot[[cntr]] <- QC.long %>%
    mutate(ID = ifelse(Subject.ID == bblid,"Poor Template ID","Adequate Template")) %>%
    mutate(size = ifelse(Subject.ID == bblid,1,.05)) %>%
    mutate(alpha = ifelse(Subject.ID == bblid,1,.1)) %>%
    filter(!(Subject.ID %in% Template.LowCNR.GrayCSF) | Subject.ID == bblid) %>%
  ggplot() + geom_point(aes(x = scanage_years,y = cnr_graycsf_lh,group = Subject.ID,color = ID,alpha = alpha,size = size)) +  geom_line(aes(x = scanage_years,y = cnr_graycsf_lh,group = Subject.ID,color = ID,alpha = alpha)) + scale_alpha_identity() + scale_size_identity() + theme(panel.grid.major = element_blank(),panel.grid.minor = element_blank(),panel.background = element_blank(),axis.line = element_line(color = "black")) + labs(x = "",y = "") + scale_color_brewer(palette = "Dark2")
  cntr <- cntr + 1
}

CNR.Gray_CSF.poorTemplate <- ggarrange(plotlist = CNR_GrayCSF_lh.plot,common.legend = TRUE,legend = "right",labels = str_c("bblid:",Template.LowCNR.GrayCSF,sep = " "),font.label = list(size = 8),label.x = .5)
annotate_figure(CNR.Gray_CSF.poorTemplate,bottom = text_grob("Age"),left = text_grob("CNR Gray-CSF Left Hemisphere",rot = 90))

### CNR Gray-CSF Right Hemisphere

Template.LowCNR.GrayCSF.rh <- QC.template %>%
  mutate(Z.cnr_graycsf_rh = as.numeric(scale(cnr_graycsf_rh))) %>%
  filter(Z.cnr_graycsf_rh < -2) %>%
  arrange(desc(Z.cnr_graycsf_rh)) %>%
  pull(bblid)

cntr <- 1
CNR_GrayCSF_rh.plot <- list()
for(bblid in Template.LowCNR.GrayCSF.rh){
  CNR_GrayCSF_rh.plot[[cntr]] <- QC.long %>%
    mutate(ID = ifelse(Subject.ID == bblid,"Poor Template ID","Adequate Template")) %>%
    mutate(size = ifelse(Subject.ID == bblid,1,.05)) %>%
    mutate(alpha = ifelse(Subject.ID == bblid,1,.1)) %>%
    filter(!(Subject.ID %in% Template.LowCNR.GrayCSF.rh) | Subject.ID == bblid) %>%
  ggplot() + geom_point(aes(x = scanage_years,y = cnr_graycsf_rh,group = Subject.ID,color = ID,alpha = alpha,size = size)) +  geom_line(aes(x = scanage_years,y = cnr_graycsf_rh,group = Subject.ID,color = ID,alpha = alpha)) + scale_alpha_identity() + scale_size_identity() + theme(panel.grid.major = element_blank(),panel.grid.minor = element_blank(),panel.background = element_blank(),axis.line = element_line(color = "black")) + labs(x = "",y = "") + scale_color_brewer(palette = "Dark2")
  cntr <- cntr + 1
}

CNR.Gray_CSF.poorTemplate.rh <- ggarrange(plotlist = CNR_GrayCSF_rh.plot,common.legend = TRUE,legend = "right",labels = str_c("bblid:",Template.LowCNR.GrayCSF.rh,sep = " "),font.label = list(size = 8),label.x = .5)
annotate_figure(CNR.Gray_CSF.poorTemplate.rh,bottom = text_grob("Age"),left = text_grob("CNR Gray-CSF Right Hemisphere",rot = 90))

### CNR Gray-White Left Hemisphere

Template.LowCNR.GrayWhite.lh <- QC.template %>%
  mutate(Z.cnr_graywhite_lh = as.numeric(scale(cnr_graywhite_lh))) %>%
  filter(Z.cnr_graywhite_lh < -2) %>%
  arrange(desc(Z.cnr_graywhite_lh)) %>%
  pull(bblid)

cntr <- 1
CNR_GrayWhite_lh.plot <- list()
for(bblid in Template.LowCNR.GrayWhite.lh){
  CNR_GrayWhite_lh.plot[[cntr]] <- QC.long %>%
    mutate(ID = ifelse(Subject.ID == bblid,"Poor Template ID","Adequate Template")) %>%
    mutate(size = ifelse(Subject.ID == bblid,1,.05)) %>%
    mutate(alpha = ifelse(Subject.ID == bblid,1,.1)) %>%
    filter(!(Subject.ID %in% Template.LowCNR.GrayWhite.lh) | Subject.ID == bblid) %>%
  ggplot() + geom_point(aes(x = scanage_years,y = cnr_graywhite_lh,group = Subject.ID,color = ID,alpha = alpha,size = size)) +  geom_line(aes(x = scanage_years,y = cnr_graywhite_lh,group = Subject.ID,color = ID,alpha = alpha)) + scale_alpha_identity() + scale_size_identity() + theme(panel.grid.major = element_blank(),panel.grid.minor = element_blank(),panel.background = element_blank(),axis.line = element_line(color = "black")) + labs(x = "",y = "") + scale_color_brewer(palette = "Dark2")
  cntr <- cntr + 1
}

CNR.Gray_White.poorTemplate.lh <- ggarrange(plotlist = CNR_GrayWhite_lh.plot,common.legend = TRUE,legend = "right",labels = str_c("bblid:",Template.LowCNR.GrayWhite.lh,sep = " "),font.label = list(size = 8),label.x = .5)
annotate_figure(CNR.Gray_White.poorTemplate.lh,bottom = text_grob("Age"),left = text_grob("CNR Gray-White Left Hemisphere",rot = 90))


### Individuals with Bad Templates, Over Time

# Labels individuals who have a poor template quality (Z-score < -2) for each measure of quality control.
QC.template.quality <- QC.template %>%
  select(-seslabel,-holes_lh,-holes_rh,-holes_total) %>%
  pivot_longer(cols = cnr_graycsf_lh:euler_total,names_to = "QC.measures",values_to = "QC.values") %>%
  group_by(QC.measures) %>%
  mutate(Z.score = as.vector(scale(QC.values))) %>%
  ungroup() %>%
  mutate(TemplateQuality = ifelse(Z.score < -2,"Poor (Z < -2)","Adequate (Z > -2)")) %>%
  select(bblid,QC.measures,TemplateQuality) %>%
  rename(Subject.ID = bblid)

# Plot which examines every session of individuals with bad templates, compared to their counterparts with adequate template quality.
QC.long %>%
  select(-holes_lh,-holes_rh,-holes_total) %>%
  pivot_longer(cols = euler_lh:cnr_graywhite_rh,names_to = "QC.measures",values_to = "QC.values") %>%
  left_join(QC.template.quality) %>%
  mutate(TemplateQuality = factor(TemplateQuality,levels = c("Adequate (Z > -2)","Poor (Z < -2)"))) %>%
  mutate(QC.measures = case_when(QC.measures == "cnr_graycsf_lh" ~ "CNR Gray-CSF Left Hemisphere",QC.measures == "cnr_graycsf_rh" ~ "CNR Gray-CSF Right Hemisphere",QC.measures == "cnr_graywhite_lh" ~ "CNR Gray-White Left Hemisphere",QC.measures == "cnr_graywhite_rh" ~ "CNR Gray-White Right Hemisphere",QC.measures == "euler_lh" ~ "Euler Left Hemisphere",QC.measures == "euler_rh" ~ "Euler Right Hemisphere",QC.measures == "euler_total" ~ "Euler Total")) %>%
  ggplot(aes(x = QC.values,color = TemplateQuality,fill = TemplateQuality)) + geom_histogram(bins = 75) + facet_wrap(~QC.measures,scales = "free_x") + scale_color_brewer(palette = "Dark2") + scale_fill_brewer(palette = "Dark2") + theme_classic() + labs(x = "",fill = "Template Quality",color = "Template Quality")

# Plots each quality control measure over time for individuals with bad templates (Z-score < -2).
QC.long %>%
  select(-holes_lh,-holes_rh,-holes_total) %>%
  pivot_longer(cols = euler_lh:cnr_graywhite_rh,names_to = "QC.measures",values_to = "QC.values") %>%
  left_join(QC.template.quality) %>%
  filter(TemplateQuality == "Poor (Z < -2)") %>%
  ggplot(aes(x = Scan.Date,y = QC.values,color = QC.measures,group = Subject.ID)) + geom_point(size = .5) + geom_line() +  facet_wrap(~QC.measures,scales = "free_y") + scale_color_brewer(palette = "Dark2")  + labs(y = "",x = "Scan Date",color = "QC measure",title = "Subjects with Low Quality Templates") + theme(axis.text.x = element_text(size = 6),panel.background = element_blank(),panel.grid = element_blank())

### Demographic plots for presentation

length(unique(Exclude.df$Subject.ID))
nrow(Exclude.df)
aggr(demo,numbers = TRUE,prop = FALSE,cex.axis = .8,oma = c(10,5,5,3))

# We started with 821 subjects, imaged over a total of 2,341 sessions. Due to poor image quality on the cross-sectional sessions, 85 sessions were excluded from further analysis. Furthermore, there are four subjects who don't have stats files for their ses-PNC1 session, so there are 88 sessions which have been removed from the original data set (since one session that didn't have a stats file was also excluded due to poor cross sectional image quality). At this stage, 801 individuals remain in the analysis. Also, there are 48 session which have missing data for race, ethnicity, and/or family id.

# Filter down dataset so we have one row per subject (scanage_years is age at first scan date for each individual)
QC.long.demo <- QC.long %>%
  group_by(Subject.ID) %>%
  arrange(Scan.Date) %>%
  ungroup() %>%
  distinct(Subject.ID,.keep_all = TRUE) %>%
  select(Subject.ID,sex:ethnicity,scanage_years) %>%
  rename(Age.FirstScan = scanage_years)

QC.long.demo %>%
  select(-Subject.ID) %>%
  rename(Sex = sex,Race = race,Ethnicity = ethnicity, "Age at first scan" = Age.FirstScan) %>%
  tbl_summary() %>%
  modify_header(label ~ "**Variable**") %>%
  modify_caption("**Subject demographics**") %>%
  bold_labels()
