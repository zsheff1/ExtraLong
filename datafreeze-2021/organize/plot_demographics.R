
library("ggplot2")
library("ggpubr")
library("dplyr")
library("viridis")
library("wesanderson")
library("RColorBrewer")
library("rstatix")
library("gt")
library("hrbrthemes")

############################### Clean Dataframes ###############################

xl <- read.csv(file.path(
    "/Users/kzoner/BBL/projects/ExtraLong/",
    "scripts/organize/datafreeze-2021/csv/",
    "ExtraLong-Datafreeze-2021-Updated-20210920.csv"
))

clean <- function(df) {

    df$scanage_years <- df$scanage_months / 12

    # Remove unnecessary columns
    df <- select(
        df,
        -c(scan_protocol, project, filename, acqid, scanage_months)
    )

    # Recode sex
    df$sex <- recode_factor(
        df$sex,
        "1" = "Male",
        "2" = "Female",
        .ordered = FALSE
    )

    # Recode race
    df$race <- recode_factor(
        df$race,
        "2" = "Black", "1" = "White",
        "5" = "Multi", "4" = "Asian",
        "3" = "Native", "6" = "Hawaiian",
        "9" = "Other",
        .missing = "Unknown", 
        .ordered = TRUE
    )

    # Recode ntimepoints
    df$ntimepoints <- factor(df$ntimepoints, ordered = TRUE)

    # Cast doscan to Date
    df$doscan <- as.Date(df$doscan)

    studies_by_date <- df %>%
        group_by(sesid) %>%
        summarize(avg_date = mean(doscan))

    studies_by_date <- studies_by_date[order(studies_by_date$avg_date), ]

    # Make study (sesid) a factor with levels by date?
    df$sesid <- factor(df$sesid, levels = studies_by_date$sesid)

    # Add column for participant numbered by age (1 being youngest)
    bblid_sorted_by_min_age <- df %>%
        group_by(bblid) %>%
        summarise(m = min(scanage_years)) %>%
        arrange(m)

    bblid_sorted_by_min_age$num_by_age <-
        as.numeric(rownames(bblid_sorted_by_min_age))

    df <- df %>% left_join(
        bblid_sorted_by_min_age %>% select(bblid, num_by_age),
        by = "bblid")

    # Add column for participant numbered by date of first scan
    bblid_sorted_by_doscan <- df %>%
        group_by(bblid) %>%
        summarise(m = min(doscan)) %>%
        arrange(m)

    bblid_sorted_by_doscan$num_by_date <-
        as.numeric(rownames(bblid_sorted_by_doscan))

    df <- df %>% left_join(
        bblid_sorted_by_doscan %>% select(bblid, num_by_date),
        by = "bblid")
        
    # Add start age, end age, and age span for each participan
    age_spans <- df %>%
        group_by(bblid) %>%
        summarize(
            start_age = min(scanage_years),
            end_age = max(scanage_years),
            age_span = end_age - start_age) %>%
        arrange(age_span, start_age)
    age_spans$num_by_span <-
        as.numeric(rownames(age_spans))

    df <- df %>% left_join(
        age_spans %>% select(bblid, start_age, end_age, age_span, num_by_span),
        by = "bblid"
    )

    # Add column for participant numbered by ntimepoints
    bblid_sorted_by_ntps <- df %>%
        group_by(num_by_span) %>%
        summarise(m = max(ntimepoints)) %>%
        arrange(m)
    bblid_sorted_by_ntps$num_by_ntps <-
        as.numeric(rownames(bblid_sorted_by_ntps))

    # Add participant num_by_ntps to df datafrae
    df <- df %>% left_join(
        bblid_sorted_by_ntps %>% select(num_by_span, num_by_ntps),
        by = "num_by_span")

    # Reorder columns
    df <- (df[c(
        "num_by_date", "num_by_age", "num_by_ntps", "num_by_span",
        "bblid", "scanid", "sesid", "doscan", "timepoint", "ntimepoints",
        "scanage_years", "sex", "race", "ethnic",
        "start_age", "end_age", "age_span"
    )])

    # Sort by age/bblid
    df <- df[order(df$num_by_age, df$timepoint), ]

    # return cleaned df
    df
}

xl <- clean(xl)

# Save helpful metrics
studies <- unique(xl$sesid)
num_subjects <- length(unique(xl$bblid))
num_sessions <- length(xl$bblid)

###############################################################################
plot_age_by <- function(df, feature, title, subtit, palette, legend, labels) {

    plot <- ggplot(
        data = df,
        aes(
            x = scanage_years,
            y = reorder(num_by_age, scanage_years, FUN = min),
            #y = num_by_age,
            color = feature
        )
    )

    plot <- plot +
        geom_point(size = .5, alpha = .6) +
        geom_line(size = .3, alpha = .5) +
        scale_x_continuous(breaks = seq(0, 70, 5)) +
        scale_y_discrete(
            breaks = seq(0, 900, 100),
            expand = expansion(add = c(10, 20))
        ) +
        labs(
            title = title,
            caption = subtit,
            x = "Age (years)",
            y = "Participant"
        ) +
        theme(legend.position = c(.8, .2)) +
        scale_color_manual(
            legend,
            values = palette,
            labels = labels
        ) +
        theme_linedraw(base_family = "IBM Plex Sans") +
        theme(
            plot.title = element_text(
                family = "IBM Plex Sans Medium",
                size = 14),
        )

    plot
}

get_legend <- function(df, feature) {
    legend <- c()
    for (val in levels(feature)) {
        count <- length(unique(xl[feature == val, ]$bblid))
        legend <- c(legend, paste0(val, " (N=", count, ")"))
    }
    legend
}
###############################################################################
######################## Plot 1: Participant Age and Sex ######################
sex_palette <- c("#F4A582", "#4393C3")

sex_subtit <- paste0(
    "N Female=",
    length(unique(xl[xl$sex == "Female", ]$num_by_age)),
    ", N Male=",
    length(unique(xl[xl$sex == "Male", ]$num_by_age)),
    ", N Total=",
    length(unique(xl$num_by_age))
)

sex_plot <- plot_age_by(
    xl, xl$sex,
    "Sex of Longitudinal Participants", NULL,
    sex_palette, "Sex", get_legend(xl, xl$sex)
)

fname <- paste0(
    "/Users/kzoner/BBL/projects/ExtraLong/",
    "scripts/organize/datafreeze-2021/plots/",
    "Longitudinal_Participants_by_Sex.pdf")

ggsave(
    sex_plot, filename = fname, 
    device = cairo_pdf, width = 7, height = 7, units = "in")

######################## Plot 2: Participant Age and Race ######################
race_palette <- c(
        "#4c705f",
        "#f7c851",
        "#dd310a",
        "#3ddffc",
        "#f79ba7",
        "#6e4481",
        "#CDC08C",
        "#F4A582"
    )

race_subtit <- paste0(
        "N White=",
        length(unique(xl[xl$race == "White", ]$num_by_age)),
        ", N Black=",
        length(unique(xl[xl$race == "Black", ]$num_by_age)),
        ", N Asian=",
        length(unique(xl[xl$race == "Asian", ]$num_by_age)),
        ", N Native=",
        length(unique(xl[xl$race == "Native", ]$num_by_age)),
        ",\nN Multi=",
        length(unique(xl[xl$race == "Multi", ]$num_by_age)),
        ", N Hawaiian=",
        length(unique(xl[xl$race == "Hawaiian", ]$num_by_age)),
        ", N Other=",
        length(unique(xl[xl$race == "Other", ]$num_by_age)),
        ", N Unknown=",
        length(unique(xl[xl$race == "Unknown", ]$num_by_age)),
        ", N Total=",
        num_subjects
    )

race_plot <- plot_age_by(
    xl, xl$race,
    "Race of Longitudinal Participants", NULL,
    race_palette, "Race", get_legend(xl, xl$race)
)
fname <- paste0(
    "/Users/kzoner/BBL/projects/ExtraLong/",
    "scripts/organize/datafreeze-2021/plots/",
    "Longitudinal_Participants_by_Race.pdf")

ggsave(
    race_plot, filename = fname, 
    device = cairo_pdf, width = 7, height = 7, units = "in")

####################### Plot 3: Participant Age and Study #####################
study_palette <- colorRampPalette(
    brewer.pal(11, "Spectral"))(length(studies))

study_subtit <- paste0(
        "N PNC=",
        nrow(xl[xl$sesid == "PNC", ]),
        ", N GRMPY=",
        nrow(xl[xl$sesid == "GRMPY", ]),
        ", N CONTE=",
        nrow(xl[xl$sesid == "CONTE", ]),
        ", N FNDM=",
        nrow(xl[xl$sesid == "FNDM", ]),
        ",\nN MOTIVE=",
        nrow(xl[xl$sesid == "MOTIVE", ]),
        ", N ONM=",
        nrow(xl[xl$sesid == "ONM", ]),
        ", N EVOL=",
        nrow(xl[xl$sesid == "EVOL", ]),
        ", N NODRA=",
        nrow(xl[xl$sesid == "NODRA", ]),
        ", N SYPR=",
        nrow(xl[xl$sesid == "SYRP", ]),
        ",\nN DAY=",
        nrow(xl[xl$sesid == "DAY", ]),
        ", N NEFF=",
        nrow(xl[xl$sesid == "NEFF", ]),
        ", N AGGY=",
        nrow(xl[xl$sesid == "AGGY", ]),
        ", N 22QMID=",
        nrow(xl[xl$sesid == "22QMID", ]),
        ", N EONSX=",
        nrow(xl[xl$sesid == "EONSX", ]),
        ", N Total=",
        num_sessions
    )

study_plot <- plot_age_by(
    xl, xl$sesid,
    "Study Involvement of Longitudinal Participants", NULL,
    study_palette, "Original Study", get_legend(xl, xl$sesid))

fname <- paste0(
    "/Users/kzoner/BBL/projects/ExtraLong/",
    "scripts/organize/datafreeze-2021/plots/",
    "Longitudinal_Participants_by_Study.pdf")

ggsave(
    study_plot, filename = fname, 
    device = cairo_pdf, width = 7, height = 7, units = "in")
##################### Plot 4: Participant's Sessions by Study ##################
plot_study <- function(df) {

    df$x_start <- lag(df$doscan, n = 1L, default = NA, order_by = df$bblid)
    df$x_end <- lead(df$doscan, n = 1L, default = NA, order_by = df$bblid)

    # Fix x_end in last timepoint for each subject
    df[df$timepoint == df$ntimepoints, ]$x_end <- NA

    # Fix x_start in first timepoint for each subject
    df[df$timepoint == 1, ]$x_start <- NA

    # Sort by participant numbered by date
    df <- df[order(df$num_by_date, df$timepoint), ]

    study_palette <- colorRampPalette(
        brewer.pal(14, "Spectral"))(length(studies))

    subtit <- paste0(
        "N PNC=",
        nrow(df[df$sesid == "PNC", ]),
        ", N GRMPY=",
        nrow(df[df$sesid == "GRMPY", ]),
        ", N CONTE=",
        nrow(df[df$sesid == "CONTE", ]),
        ", N FNDM=",
        nrow(df[df$sesid == "FNDM", ]),
        ",\nN MOTIVE=",
        nrow(df[df$sesid == "MOTIVE", ]),
        ", N ONM=",
        nrow(df[df$sesid == "ONM", ]),
        ", N EVOL=",
        nrow(df[df$sesid == "EVOL", ]),
        ", N NODRA=",
        nrow(df[df$sesid == "NODRA", ]),
        ", N SYPR=",
        nrow(df[df$sesid == "SYRP", ]),
        ",\nN DAY=",
        nrow(df[df$sesid == "DAY", ]),
        ", N NEFF=",
        nrow(df[df$sesid == "NEFF", ]),
        ", N AGGY=",
        nrow(df[df$sesid == "AGGY", ]),
        ", N 22QMID=",
        nrow(df[df$sesid == "22QMID", ]),
        ", N EONSX=",
        nrow(df[df$sesid == "EONSX", ]),
        ", N Total=",
        nrow(df)
    )

    study_plot <- ggplot(
        data = df,
        aes(
            x = doscan,
            y = reorder(num_by_date, doscan, FUN = min),
            color = sesid
        )
    )

    # Add labels, legend, scale x and y
    study_plot <- study_plot +
        geom_segment(
            aes(x = x_start, xend = doscan,
                y = num_by_date, yend = num_by_date),
            size = .3,
            alpha = .4) +
        geom_point(
            size = 1, alpha = .5) +
        scale_color_manual(
            values = study_palette,
            labels = studies
        ) +
        scale_x_date(
            date_breaks = "1 year", date_labels = "%Y") +
        scale_y_discrete(
            breaks = seq(0, 900, 100)) +
        labs(
            title = "Studies in ExtraLong 2021",
            subtitle = subtit,
            x = "Date of Scan",
            y = "Participant"
        ) +
        theme(legend.position = c(.8, .2)) +
        theme_linedraw()

    study_plot
}

plot_study(xl)
################## Plot 4: Participant Age Span by ntimepoints  ################
plot_tps <- function(title, subtit, legend, labels) {

    bblid_by_ntimepoints <- distinct(xl %>% select(
        c(
            "bblid", "ntimepoints", "age_span",
            "start_age", "end_age", "num_by_ntps")
    ))

    bblid_by_ntimepoints <- bblid_by_ntimepoints %>%
        arrange(ntimepoints)

    df <- bblid_by_ntimepoints

    plot <- ggplot(
        data = df
    )

    plot <- plot +
        geom_segment(
            aes(x = 0, xend = age_span,
                y = num_by_ntps, yend = num_by_ntps,
                color = factor(ntimepoints)),
            size = .3,
            alpha = .4,
            lineend = "round") +
        scale_y_continuous(
            breaks = seq(0, 900, 100)) +
        scale_x_continuous(
            breaks = seq(0, 12, 1), expand = expansion(mult = 0.05)) +
        scale_color_brewer(
            legend,
            palette = "Spectral",
            labels = labels
        ) +
        labs(
            title = title,
            subtitle = subtit,
            x = "Age Span (years)",
            y = "Participant"
        ) +
        theme(legend.position = c(.8, .2)) +
        theme_linedraw(base_family = "IBM Plex Sans") +
        theme(
            plot.title = element_text(
                family = "IBM Plex Sans Medium",
                size = 14),
        )

    plot
}
subtit <- paste0(
        "Two Sessions=",
        length(unique(xl[xl$ntimepoints == 2, ]$num_by_ntps)),
        ", Three Sessions=",
        length(unique(xl[xl$ntimepoints == 3, ]$num_by_ntps)),
        ", Four Sessions=",
        length(unique(xl[xl$ntimepoints == 4, ]$num_by_ntps)),
        ",\nFive Sessions=",
        length(unique(xl[xl$ntimepoints == 5, ]$num_by_ntps)),
        ", Six Sessions=",
        length(unique(xl[xl$ntimepoints == 6, ]$num_by_ntps)),
        ", Seven Sessions=",
        length(unique(xl[xl$ntimepoints == 7, ]$num_by_ntps)),
        ",\nEight Sessions=",
        length(unique(xl[xl$ntimepoints == 8, ]$num_by_ntps)),
        ", Nine Sessions=",
        length(unique(xl[xl$ntimepoints == 9, ]$num_by_ntps)),
        ", Ten Sessions=",
        length(unique(xl[xl$ntimepoints == 10, ]$num_by_ntps)),
        ", Eleven Sessions=",
        length(unique(xl[xl$ntimepoints == 11, ]$num_by_ntps)),
        ",\nN Total=",
        num_sessions

)
tp_plot <- plot_tps(
    "Participant Age Spans and Session Counts",
    NULL,
    "Num Sessions", get_legend(xl, xl$ntimepoints)
)

fname <- paste0(
    "/Users/kzoner/BBL/projects/ExtraLong/",
    "scripts/organize/datafreeze-2021/plots/",
    "Longitudinal_Participants_by_Timepoints.pdf")

ggsave(
    tp_plot, filename = fname, 
    device = cairo_pdf, width = 7, height = 7, units = "in")

##############################################################################
# SUMMARY TABLES?

# Compute summary statistics
summary.stats <- xl %>%
  group_by(dose) %>%
  get_summary_stats() %>%
  select(dose, n, median, iqr)
summary.stats

##############################################################################

##############################################################################
pdf(file = paste0(
    "/Users/kzoner/BBL/projects/ExtraLong/",
    "scripts/organize/datafreeze-2021/plots/",
    "Longitudinal_Participants_by_Race.pdf"))


dev.off()

##############################################################################
# WIP: 
##############################################################################
wip <- function(){
        lame_tps <- function() {

        bblid_by_ntimepoints <- distinct(xl %>% select(
            c(
                "bblid", "ntimepoints", "age_span",
                "start_age", "end_age", "num_by_span")
        ))

        bblid_by_ntimepoints <- bblid_by_ntimepoints %>%
            group_by(ntimepoints) %>%
            arrange(age_span)

        df <- bblid_by_ntimepoints

        plot <- ggplot(
            data = df
        )

        plot <- plot +
            geom_segment(
                aes(x = start_age, xend = end_age,
                    y = num_by_span, yend = num_by_span,
                    color = age_span),
                size = .3,
                alpha = .4,
                lineend = "round") +
            scale_y_discrete(
                breaks = seq(0, 900, 100)) +
            scale_x_continuous(
                breaks = seq(0, 70, 5)) +
            scale_color_viridis(
            ) +
            labs(
                title = "Participants by ntimepoints",
                #subtitle = subtit,
                x = "Age Span (years)",
                y = "Participant"
            ) +
            theme(legend.position = c(.8, .2)) +
            theme_linedraw()

        plot
    }

    lame_tps()

    bad_tps <- function(df) {


        palette <- colorRampPalette(
            brewer.pal(11, "Spectral"))(max(df$scanage_years))

        tp_plot <- ggplot(
            data = df,
            aes(
                x = scanage_years,
                y = reorder(num_by_ntps, ntimepoints, FUN = min),
                color = factor(ntimepoints, levels = c(2,3,4,5,6))
            )
        )

        tp_plot <- tp_plot +
            #geom_point(size = .6, alpha = .8) +
            geom_line(size = .4, alpha = .4) +
            scale_x_continuous(breaks = seq(0, 30, 5), limits = c(8, 30)) +
            scale_y_discrete(breaks = seq(0, 900, 100)) +
            labs(
                title = "Number of Timepoints for ExtraLong Participants",
                #subtitle = subtit,
                x = "Age (years)",
                y = "Participant"
            ) +
            scale_color_viridis(
                discrete = TRUE
            ) +
            theme(legend.position = c(.8, .2)) +
            theme_linedraw()

        tp_plot
    }

    bad_tps(xl)

    ##############################################################################
    plot_sessions_by <- function(df, feature, title, subtit, palette, labels) {

        df$x_start <- lag(df$doscan, n = 1L, default = NA, order_by = df$bblid)
        df$x_end <- lead(df$doscan, n = 1L, default = NA, order_by = df$bblid)

        # Fix x_end in last timepoint for each subject
        df[df$timepoint == df$ntimepoints, ]$x_end <- NA

        # Fix x_start in first timepoint for each subject
        df[df$timepoint == 1, ]$x_start <- NA

        # Sort by participant numbered by date
        df <- df[order(df$num_by_date, df$timepoint), ]

        study_plot <- ggplot(
            data = df,
            aes(
                x = doscan,
                y = reorder(num_by_date, doscan, FUN = min),
                color = factor(feature)
            )
        )

        # Add labels, legend, scale x and y
        study_plot <- study_plot +
            geom_segment(
                aes(x = x_start, xend = doscan,
                    y = num_by_date, yend = num_by_date),
                size = .3,
                alpha = .4) +
            geom_point(
                size = 1, alpha = .5) +
            scale_color_manual(
                values = palette
                # labels = labels
            ) +
            scale_x_date(
                date_breaks = "1 year", date_labels = "%Y") +
            scale_y_discrete(
                breaks = seq(0, 900, 100)) +
            labs(
                title = title,
                subtitle = subtit,
                x = "Date of Scan",
                y = "Participant"
            ) +
            theme(legend.position = c(.8, .2)) +
            theme_linedraw()

        study_plot
    }

    study_palette <- colorRampPalette(
        brewer.pal(14, "Spectral"))(length(studies))

    plot_sessions_by(
        xl, xl$sesid,
        "Sessions by Study in ExtraLong 2021", study_subtit,
        study_palette, studies
    )

    palette <- colorRampPalette(
        brewer.pal(11, "Spectral"))(11)

    plot_sessions_by(
        xl, xl$ntimepoints,
        "Ntimepoints in ExtraLong 2021", study_subtit,
        palette
    )
    ####

    tail(xl)

}