for dir in /project/ExtraLong/scratch/scitran/bbl/MIND_856432/*/; do
    [[ "${dir}" =~ /([0-9]+)_([0-9]+)/ ]] || continue
    sub="${BASH_REMATCH[1]}"
    ses="${BASH_REMATCH[2]}"
    sub_pad="$(printf '%06d' "${sub}")"
    ses_pad="$(printf '%05d' "${ses}")"
    apptainer run --cleanenv \
        -B /project/ExtraLong/scratch/scitran/bbl/MIND_856432 \
        -B /project/ExtraLong/code/curate/heuristic_mind.py:/heuristic.py \
        /project/bbl_gur_evolpsy/code/bids/heudiconv_1.3.2.sif \
        --files /project/ExtraLong/scratch/scitran/bbl/MIND_856432/${sub}_${ses}/BRAIN\ RESEARCH\^ROALF/*/*.dicom.zip \
        --grouping all \
        -f /heuristic.py \
        -c dcm2niix \
        -o /project/ExtraLong/scratch/scitran/bbl/MIND_856432 \
        -b \
        -s ${sub_pad} \
        -ss ${ses_pad} \
        --minmeta
done