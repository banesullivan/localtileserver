"""Tests for localtileserver.tiler.palettes -- especially the colormap registry."""

import pytest

from localtileserver.tiler.palettes import (
    get_registered_colormap,
    palette_valid_or_raise,
    register_colormap,
)


class TestColormapRegistry:
    def test_register_and_retrieve(self):
        cmap_data = {0: (0, 0, 0, 255), 127: (128, 128, 128, 255), 255: (255, 255, 255, 255)}
        key = register_colormap(cmap_data)
        assert key.startswith("custom:")
        retrieved = get_registered_colormap(key)
        assert retrieved == cmap_data

    def test_same_data_same_hash(self):
        cmap_data = {0: (0, 0, 0, 255), 1: (255, 255, 255, 255)}
        key1 = register_colormap(cmap_data)
        key2 = register_colormap(cmap_data)
        assert key1 == key2

    def test_different_data_different_hash(self):
        key1 = register_colormap({0: (0, 0, 0, 255)})
        key2 = register_colormap({0: (255, 0, 0, 255)})
        assert key1 != key2

    def test_get_nonexistent_key(self):
        assert get_registered_colormap("custom:doesnotexist") is None

    def test_get_non_custom_key(self):
        assert get_registered_colormap("viridis") is None


class TestPaletteValidOrRaise:
    def test_valid_rio_cmap(self):
        palette_valid_or_raise("viridis")

    def test_invalid_cmap_raises(self):
        with pytest.raises(ValueError, match="Invalid"):
            palette_valid_or_raise("not_a_real_colormap")

    def test_valid_custom_registered(self):
        key = register_colormap({0: (0, 0, 0, 255)})
        palette_valid_or_raise(key)

    def test_invalid_custom_unregistered(self):
        with pytest.raises(ValueError, match="not found"):
            palette_valid_or_raise("custom:doesnotexist")
