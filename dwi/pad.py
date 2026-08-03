#!/usr/bin/env python3

import nibabel as nib
import numpy as np
import sys

# parse arguments
input_path = sys.argv[1]
output_path = sys.argv[2]
pad_width = [(int(sys.argv[i]), int(sys.argv[i + 1])) for i in range(3, len(sys.argv)-1, 2)]

# load input image
img = nib.load(input_path)
data = img.get_fdata(dtype=np.float32)

# pad the data
padded_data = np.pad(data, pad_width, mode='constant', constant_values=0)

# save output image
padded_img = nib.Nifti1Image(padded_data, affine=img.affine, header=img.header)
nib.save(padded_img, output_path)