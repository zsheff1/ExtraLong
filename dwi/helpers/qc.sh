get_mean_projection_distance() {
    module load fsl/6.0.3

    local scratch_base=""
    local fa_map=""
    local mean_fa=""
    local dst_map=""
    local mask=""

    local options
    options=$(getopt \
        --options s:f:F:d:m: \
        --longoptions scratch:,fa_map:,mean_fa:,dst_map:,mask: \
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
            -f|--fa_map)
                fa_map="$2"
                shift 2
                ;;
            -F|--mean_fa)
                mean_fa="$2"
                shift 2
                ;;
            -d|--dst_map)
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

    if [[ -z "${scratch_base}" || -z "${fa_map}" || -z "${mean_fa}" || -z "${dst_map}" || -z "${mask}" ]]; then
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
        "${FSLDIR}/data/standard/LowerCingulum_1mm" \
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
    module load fsl/6.0.3
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
    module load fsl/6.0.3
    module load afni_openmp/20.1

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

    module load fsl/6.0.3
    module load afni_openmp/20.1

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