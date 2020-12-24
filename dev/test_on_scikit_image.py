"""

# Logic to test if lazy loading works on scikit image

mkdir -p $HOME/tmp/lazy-init-test
cd $HOME/tmp/lazy-init-test
git clone https://github.com/scikit-image/scikit-image.git
cd $HOME/tmp/lazy-init-test/scikit-image
python setup.py build_ext --inplace


python -c "import skimage; print(skimage.__file__)"

mkinit skimage/filters/__init__.py --relative --lazy
"""
