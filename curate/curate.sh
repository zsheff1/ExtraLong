for project_label in MIND_856432 SSBC_844685 RSVP_855714 22q_Midline_834246; do
    for dir in /project/ExtraLong/scratch/${project_label}/*/; do
        [[ "${dir}" =~ /([0-9]+)_([0-9]+)/ ]] || continue
        sub="${BASH_REMATCH[1]}"
        ses="${BASH_REMATCH[2]}"
        sub_pad="$(printf '%06d' "${sub}")"
        ses_pad="$(printf '%05d' "${ses}")"
        apptainer run --cleanenv \
            -B /project/ExtraLong/scratch/${project_label} \
            -B /project/ExtraLong/code/curate/heuristic_mind.py:/heuristic.py \
            /project/bbl_gur_evolpsy/code/bids/heudiconv_1.3.2.sif \
            --files /project/ExtraLong/scratch/${project_label}/${sub}_${ses}/BRAIN\ RESEARCH\^ROALF/*/*.dicom.zip \
            --grouping all \
            -f /heuristic.py \
            -c dcm2niix \
            -o /project/ExtraLong/scratch/${project_label} \
            -b \
            -s ${sub_pad} \
            -ss ${ses_pad} \
            --minmeta
    done
done

project_label=MIND_856432
for dir in /project/ExtraLong/scratch/${project_label}/*/; do
    [[ "${dir}" =~ /([0-9]+)_([0-9]+)/ ]] || continue
    sub="${BASH_REMATCH[1]}"
    ses="${BASH_REMATCH[2]}"
    sub_pad="$(printf '%06d' "${sub}")"
    ses_pad="$(printf '%05d' "${ses}")"
    apptainer run --cleanenv \
        -B /project/ExtraLong/scratch/${project_label} \
        -B /project/ExtraLong/code/curate/heuristic_mind.py:/heuristic.py \
        /project/bbl_gur_evolpsy/code/bids/heudiconv_1.3.2.sif \
        --files /project/ExtraLong/scratch/${project_label}/${sub}_${ses}/BRAIN\ RESEARCH\^ROALF/*/*.dicom.zip \
        --grouping all \
        -f /heuristic.py \
        -c dcm2niix \
        -o /project/ExtraLong/scratch/${project_label} \
        -b \
        -s ${sub_pad} \
        -ss ${ses_pad} \
        --minmeta
done