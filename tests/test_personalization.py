import pytest
from sonny.personalization import DashboardBlock, Personalization


def test_owner_can_rearrange_and_select_avatar():
    initial = Personalization("customer-a")
    updated = initial.update("customer-a", avatar="friendly", theme="light",
                             blocks=[DashboardBlock("voice", 0, 0, 4, 2),
                                     DashboardBlock("github", 4, 0, 4, 2)])
    assert updated.avatar == "friendly"
    assert updated.blocks[1].x == 4
    assert initial.blocks == ()


def test_other_customer_cannot_update():
    with pytest.raises(PermissionError):
        Personalization("customer-a").update("customer-b", avatar="minimal")


@pytest.mark.parametrize("key", ["untrusted_html", "admin_controls", ""])
def test_unrecognized_blocks_rejected(key):
    with pytest.raises(ValueError):
        DashboardBlock(key, 0, 0)


def test_overlapping_blocks_rejected():
    with pytest.raises(ValueError):
        Personalization("a", blocks=(DashboardBlock("voice", 0, 0),
                                      DashboardBlock("github", 2, 1)))


def test_invalid_bounds_and_duplicate_blocks_rejected():
    with pytest.raises(ValueError):
        DashboardBlock("voice", 11, 0, 2, 2)
    with pytest.raises(ValueError):
        Personalization("a", blocks=(DashboardBlock("voice", 0, 0),
                                      DashboardBlock("voice", 4, 0)))


def test_unsupported_avatar_rejected():
    with pytest.raises(ValueError):
        Personalization("a", avatar="<script>")
