"""

# Logic to test if lazy loading works on scikit image

mkdir -p $HOME/tmp/lazy-init-test
cd $HOME/tmp/lazy-init-test
git clone https://github.com/scikit-image/scikit-image.git
cd $HOME/tmp/lazy-init-test/scikit-image
python setup.py build_ext --inplace


python -c "import skimage.filters; print(skimage.filters.__file__)"
python -c "import skimage; print(skimage.__file__)"

cat skimage/filters/__init__.py

echo "
__private__ = ['setup']
__protected__ = ['rank']

__submodules__ = [
    'rank',
    'lpi_filter',
    '_gaussian',
    'edges',
    '_rank_order',
    '_gabor',
    'thresholding',
    'ridges',
    '_median',
    '_sparse',
    '_unsharp_mask',
    '_window',
]
# End of custom init code" > skimage/filters/__init__.py
# mkinit skimage/filters/__init__.py --relative --lazy --nomods -w --lazy_boilerplate="from ..util.lazy import lazy_import"
mkinit skimage/filters/__init__.py --relative --lazy --nomods -w

cat skimage/filters/__init__.py

python -c "from skimage import filters; print(repr(filters.equalize))"
python -c "import skimage; print(skimage.filters)"
"""

"""


mkinit ./networkx/algorithms --recursive --black -w

"""
