module load apptainer

dir_scratch=/project/ExtraLong/scratch
container=/project/ExtraLong/code/curate/heudiconv_1.4.0.sif

for project_label in MIND_856432 SSBC_844685 RSVP_855714 22q_Midline_834246; do
    dir_project="${dir_scratch}/${project_label}"
    [[ -d ${dir_project} ]] || continue
    for dir in ${dir_project}/*/; do
        [[ "${dir}" =~ /([0-9]+)_([0-9]+)/ ]] || continue
        sub="${BASH_REMATCH[1]}"
        ses="${BASH_REMATCH[2]}"
        sub_pad="$(printf '%06d' "${sub}")"
        ses_pad="$(printf '%05d' "${ses}")"
        apptainer run --cleanenv \
            -B ${dir_project} \
            ${container} \
            --files ${dir_project}/${sub}_${ses}/*/*.dicom.zip \
            --grouping all \
            -f convertall \
            -c none \
            -o ${dir_project} \
            -s ${sub_pad} \
            -ss ${ses_pad}
    done
    mapfile -d '' files < <(
        find ${dir_project}/.heudiconv/*/info \
            -type f \
            -name 'dicominfo*.tsv' \
            -print0
    )
    head -n 1 "${files[0]}" > ${dir_scratch}/dicominfo_${project_label}.tsv
    for file in "${files[@]}"; do
        tail -n +2 "${file}" >> ${dir_scratch}/dicominfo_${project_label}.tsv
    done
done