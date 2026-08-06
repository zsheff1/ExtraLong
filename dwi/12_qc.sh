#!/bin/bash
#BSUB -o /project/bbl_gur_evolpsy/code/logs/dwi/tbss/enigma_qc.o
#BSUB -e /project/bbl_gur_evolpsy/code/logs/dwi/tbss/enigma_qc.e
#BSUB -J enigma_qc

get_mean_projection_distance() {
    local scratch_base=""
    local fsl_dir=""
    local fa_map=""
    local mean_fa=""
    local dst_map=""
    local mask=""

    local options
    options=$(getopt \
        --options s:d:f:F:D:m: \
        --longoptions scratch:,fsl_dir:,fa_map:,mean_fa:,dst_map:,mask: \
        --name "$0" \
        -- "$@"
    ) || return 64

    eval set -- "$options"

    while true; do
        case "$1" in
            -s|--scratch)
                scratch_base="$2"
                shift 2
                ;;
            -d|--fsl_dir)
                fsl_dir="$2"
                shift 2
                ;;
            -f|--fa_map)
                fa_map="$2"
                shift 2
                ;;
            -F|--mean_fa)
                mean_fa="$2"
                shift 2
                ;;
            -D|--dst_map)
                dst_map="$2"
                shift 2
                ;;
            -m|--mask)
                mask="$2"
                shift 2
                ;;
            --)
                shift
                break
                ;;
            *)
                echo "Unexpected argument: $1" >&2
                return 64
                ;;
        esac
    done

    if [[ -z "${scratch_base}" || -z "${fsl_dir}" || -z "${fa_map}" || -z "${mean_fa}" || -z "${dst_map}" || -z "${mask}" ]]; then
        return 64
    fi

    local scratch_dir
    scratch_dir=$(mktemp -d "${scratch_base}_XXXXXX")
	trap 'rm -rf "${scratch_dir}"' RETURN

    # get Proj Dist images
    tbss_skeleton \
        -d \
        -i "${mean_fa}" \
        -p 0.2 \
        "${dst_map}" \
        "${fsl_dir}/data/standard/LowerCingulum_1mm" \
        "${fa_map}" \
        "${scratch_dir}/dst_vals"

    local direction input output
    for direction in X Y Z; do
        input="${scratch_dir}/dst_vals_search_${direction}.nii.gz"
        output="${scratch_dir}/squared_${direction}.nii.gz"
        fslmaths "${input}" -mul "${input}" "${output}"
    done

    #Overall displacement
    local proj_dist
    proj_dist="${scratch_dir}/total_projection_distance.nii.gz"
    fslmaths \
        "${scratch_dir}/squared_X.nii.gz" \
        -add "${scratch_dir}/squared_Y.nii.gz" \
        -add "${scratch_dir}/squared_Z.nii.gz" \
        -sqrt \
        "${proj_dist}"

    # store extracted distances
    local mean
    mean=$(fslstats -t "${proj_dist}" -k "${mask}" -m)
    echo "${mean}"
}

get_volumes() {
    local image=""

    local options
    options=$(getopt \
        --options i: \
        --longoptions image: \
        --name "$0" \
        -- "$@"
    ) || return 64

    eval set -- "$options"

    while true; do
        case "$1" in
            -i|--image)
                image="$2"
                shift 2
                ;;
            --)
                shift
                break
                ;;
            *)
                echo "Unexpected argument: $1" >&2
                return 64
                ;;
        esac
    done

    if [[ -z "${image}" ]]; then
        return 64
    fi

    local dim4
    read -r _ dim4 < <(fslinfo "${image}" | grep "^dim4")
    echo "${dim4}"
}

get_tsnr_b0() {
    local scratch_base=""
    local raw=""

    local options
    options=$(getopt \
        --options s:r \
        --longoptions scratch:,raw: \
        --name "$0" \
        -- "$@"
    ) || return 64

    eval set -- "$options"

    while true; do
        case "$1" in
            -s|--scratch)
                scratch_base="$2"
                shift 2
                ;;
            -r|--raw)
                raw="$2"
                shift 2
                ;;
            --)
                shift
                break
                ;;
            *)
                echo "Unexpected argument: $1" >&2
                return 64
                ;;
        esac
    done

    if [[ -z "${scratch_base}" || -z "${raw}" ]]; then
        return 64
    fi

    local scratch_dir
    scratch_dir=$(mktemp -d "${scratch_base}_XXXXXX")
	trap 'rm -rf "${scratch_dir}"' RETURN

    module load fsl
    module load afni_openmp

    ulimit -c 0

    mapfile -t niftis < <(find "${raw}" -mindepth 1 -maxdepth 1 -type f -name "*dwi.nii.gz")
    mapfile -t bvals < <(find "${raw}" -mindepth 1 -maxdepth 1 -type f -name "*dwi.bval")
    mapfile -t bvecs < <(find "${raw}" -mindepth 1 -maxdepth 1 -type f -name "*dwi.bvec")

    if [[ "${#niftis[@]}" == 1 && "${#bvals[@]}" == 1 && "${#bvecs[@]}" == 1 ]]; then
        nifti="${niftis[0]}"
        bval="${bvals[0]}"
        bvec="${bvecs[0]}"
    elif [[ "${#niftis[@]}" > 1 && "${#bvals[@]}" > 1 && "${#bvecs[@]}" > 1 ]]; then
        nifti="${scratch_dir}/dwi.nii.gz"
        bval="${scratch_dir}/dwi.bval"
        bvec="${scratch_dir}/dwi.bvec"
        fslmerge -t "${nifti}" "${nifti_inputs[@]}"
        paste -d " " "${bvals[@]}" > "${bval}"
        paste -d " " "${bvecs[@]}" > "${bvec}"
    else
        return 1
    fi

    /project/bbl_projects/apps/melliott/scripts/qa_dti_v4.sh \
    "${nifti}" \
    "${bval}" \
    "${bvec}" \
    100 \
    "${scratch_dir}/results.txt"

    local tsnr_b0
    read -r _ tsnr_b0 < <(grep "tsnr_b0" "${scratch_dir}/results.txt")
    echo "${tsnr_b0}"
}

# Emma Sprooten for ENIGMA-DTI
# run in a new directory eg. Proj_Dist/
# create a text file containing paths to your masked FA maps
# output in Proj_Dist.txt

module load fsl/6.0.3

###### USER INPUTS ###############
## insert main folder where you ran TBSS
## just above "stats/" and "FA/"
maindir="/project/bbl_gur_evolpsy/derivatives/dwi"

## insert full path to mean_FA, skeleton mask and distance map
## based on ENIGMA-DTI protocol this should be:
mean_fa="${maindir}/stats/mean_FA.nii.gz"
mask="${maindir}/stats/mean_FA_skeleton_mask.nii.gz"
dst_map="${maindir}/stats/mean_FA_skeleton_mask_dst.nii.gz"

##############
### from here it should be working without further adjustments

echo "participant_id,session_id,mean_projection_distance,volumes,tsnr_b0" > "${maindir}/stats/proj_dist.csv"

## for each FA map
while read -r sub; do

    base=$(basename "${sub}" ".nii.gz")
    [[ base =~ sub-([0-9]{6})_ses-([0-9]{5}) ]]
    participant_id="${BASH_REMATCH[1]}"
    session_id="${BASH_REMATCH[2]}"

    fa_map="${sub%%.nii.gz}_fa.nii.gz"
    preproc="${sub%%_diffeo.nii.gz}_space-ACPC_desc-preproc_dwi.nii.gz"

    mean_projection_distance=$(
        get_mean_projection_distance \
        --scratch "/scratch" \
        --fsl_dir "${FSLDIR}" \
        --fa_map "${fa_map}" \
        --mean_fa "${mean_fa}" \
        --dst_map "${dst_map}" \
        --mask "${mask}" \
    )
    volumes=$(
        get_volumes \
        --image "${preproc}"
    )
    tsnr_b0=$(
        get_tsnr_b0 \
        --scratch "\scratch" \
        --raw "${DATA_DIR}/${sub}/${ses}/dwi"
    )

    echo "${participant_id},${session_id},${mean_projection_distance},${volumes},${tsnr_b0}" >> "${maindir}/stats/proj_dist.csv"
done < "${SUBJECTSFILE}"
