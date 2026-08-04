#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/dwi.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${LOG_DIR}/${script_stem}"

jobscript_path="${JOBSCRIPT_DIR}/${script_stem}.sh"

FSL_DIR="\${FSLDIR}/data/atlases/JHU"
TARGET_FA="mean_FA.nii.gz"
ATLAS_FA="JHU-ICBM-FA-2mm.nii.gz"
ATLAS_TRACTS="JHU-ICBM-tracts-maxprob-thr25-2mm.nii.gz"
ATLAS_LABELS="JHU-ICBM-labels-2mm.nii.gz"
PAD="18 19 9 10 18 19"

cat <<-EOF > "${jobscript_path}"
#!/bin/bash
#BSUB -J ${script_stem}
#BSUB -o ${LOG_DIR}/${script_stem}/${script_stem}.o
#BSUB -e ${LOG_DIR}/${script_stem}/${script_stem}.e

module load afni_openmp/20.1
module load ANTs/2.3.5
module load fsl/6.0.3

mkdir -p ${ATLAS_DIR}
mkdir -p ${ROI_DIR}

# pad, flip from RPI to LPI, center: for JHU FA and atlas
for atlas in "${ATLAS_FA}" "${ATLAS_TRACTS}" "${ATLAS_LABELS}"; do
    cp "${FSL_DIR}/${atlas}" "${ATLAS_DIR}/${atlas}"
    ${PAD_EXECUTABLE} "${ATLAS_DIR}/${atlas}" "${ATLAS_DIR}/${atlas}" ${PAD}
    fslswapdim "${ATLAS_DIR}/${atlas}" -x y z "${ATLAS_DIR}/${atlas}"
    if [[ "${atlas}" == "${ATLAS_TRACTS}" || "${atlas}" == "${ATLAS_LABELS}" ]]; then
        fslmaths "${ATLAS_DIR}/${atlas}" "${ATLAS_DIR}/${atlas}" -odt char
    fi
    fslorient -swaporient "${ATLAS_DIR}/${atlas}"
    3drefit -xorigin 0 -yorigin 0 -zorigin 0 "${ATLAS_DIR}/${atlas}"
done

# rigid and affine registration of FA map to mean space
antsRegistration \\
    --dimensionality 3 \\
    --output "${ATLAS_DIR}/ICBM2POP_" \\
    --interpolation Linear \\
    --transform Rigid[0.1] \\
    --metric MI["${STATS_DIR}/${TARGET_FA}", "${ATLAS_DIR}/${ATLAS_FA}", 1, 32, Regular, 0.25] \\
    --convergence [500x250x100, 1e-6, 10] \\
    --shrink-factors 4x2x1 \\
    --smoothing-sigmas 2x1x0vox \\
    --transform Affine[0.1] \\
    --metric MI["${STATS_DIR}/${TARGET_FA}", "${ATLAS_DIR}/${ATLAS_FA}", 1, 32, Regular, 0.25] \\
    --convergence [500x250x100, 1e-6, 10] \\
    --shrink-factors 4x2x1 \\
    --smoothing-sigmas 2x1x0vox

# nonlinear registration of FA map to mean space
antsRegistration \\
    --dimensionality 3 \\
    --initial-moving-transform "${ATLAS_DIR}/ICBM2POP_0GenericAffine.mat" \\
    --output "${ATLAS_DIR}/ICBM2POP_" \\
    --interpolation Linear \\
    --transform SyN[0.1,3,0] \\
    --metric CC["${STATS_DIR}/${TARGET_FA}", "${ATLAS_DIR}/${ATLAS_FA}", 1, 4] \\
    --convergence [100x70x50, 1e-6, 10] \\
    --shrink-factors 4x2x1 \\
    --smoothing-sigmas 2x1x0vox

# apply these transforms to the atlas, moving it to template space
antsApplyTransforms \\
    -d 3 \\
    -i ${ATLAS_DIR}/${ATLAS_TRACTS} \\
    -r ${STATS_DIR}/${TARGET_FA} \\
    -o ${ATLAS_DIR}/${ATLAS_TRACTS//ICBM/POP} \\
    -t ${ATLAS_DIR}/ICBM2POP_1Warp.nii.gz \\
    -t ${ATLAS_DIR}/ICBM2POP_0GenericAffine.mat \\
    -n GenericLabel

# apply these transforms to the atlas, moving it to template space
antsApplyTransforms \\
    -d 3 \\
    -i ${ATLAS_DIR}/${ATLAS_LABELS} \\
    -r ${STATS_DIR}/${TARGET_FA} \\
    -o ${ATLAS_DIR}/${ATLAS_LABELS//ICBM/POP} \\
    -t ${ATLAS_DIR}/ICBM2POP_1Warp.nii.gz \\
    -t ${ATLAS_DIR}/ICBM2POP_0GenericAffine.mat \\
    -n GenericLabel

# break tracts up into a volume for each region
for i in \$(seq 1 \$(fslstats ${FSL_DIR}/${ATLAS_TRACTS} -R | awk '{print int(\$2)}')); do
    printf -v padded "%02d" \${i}

    fslmaths ${ATLAS_DIR}/${ATLAS_TRACTS//ICBM/POP} \\
        -thr \${i} -uthr \${i} -bin \\
        ${ROI_DIR}/roi_tracts_\${padded}.nii.gz \\
        -odt char
done

# break labels up into a volume for each region
for i in \$(seq 1 \$(fslstats ${FSL_DIR}/${ATLAS_LABELS} -R | awk '{print int(\$2)}')); do
    printf -v padded "%02d" \${i}

    fslmaths ${ATLAS_DIR}/${ATLAS_LABELS//ICBM/POP} \\
        -thr \${i} -uthr \${i} -bin \\
        ${ROI_DIR}/roi_labels_\${padded}.nii.gz \\
        -odt char
done
EOF

chmod 775 "${jobscript_path}"
bsub < "${jobscript_path}"
