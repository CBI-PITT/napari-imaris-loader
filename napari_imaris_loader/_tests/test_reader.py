import os
from napari_imaris_loader import napari_get_reader


# tmp_path is a pytest fixture
def test_reader(tmp_path='brain_crop3.ims'):
    """An example of how you might test your plugin."""
    
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)),tmp_path)
    # Test whether we get a callable reader function
    #reader = napari_get_reader('/path/to/a/fake.ims')
    reader = napari_get_reader(path)
    assert callable(reader)

    # make sure we're delivering the right format
    layer_data = reader(path)
    assert isinstance(layer_data, list)
    assert isinstance(layer_data[0], tuple) and len(layer_data[0]) == 2
    assert isinstance(layer_data[0][0], list) and isinstance(layer_data[0][1], dict)


def test_get_reader_pass():
    reader = napari_get_reader("fake.file")
    assert reader is None
