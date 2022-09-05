#   Copyright 2022-present Michael Hall
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


# With thanks to the community for sourcing enough data and reversing the equations to a high degree of certainty
# And especially the work of those in the allagan studies discord.


# This file currently has some lv 90 dancer specific simplifications and should be expanded to have further job support in the future.

from __future__ import annotations

from typing import NamedTuple


class DancerStats(NamedTuple):
    wd: int
    w_delay: float
    dex: int
    crit: int
    det: int
    dh: int
    sks: int


class DamageInfo(NamedTuple):
    hit: int | float
    crit_hit: int | float
    dh_hit: int | float
    crit_dh_hit: int | float
    crit_rate: float
    dh_rate: float


# formulas from Allagan Studies, with some simplifications made.
def f_wd(wd: int) -> int:
    # (stats.wd + (M * job_mod // 1000)) simplifies to the below for lv 90 dancer
    return wd + 44


def f_ap(dex: int) -> int:
    return 100 + (dex - 390) * 195 // 390


def f_det(det: int) -> int:
    return 140 * (det - 390) // 1900 + 1000


def f_crit(crit: int) -> int:
    return 200 * (crit - 400) // 1900 + 1400


def f_sks(sks: int) -> int:
    return 130 * (sks - 400) // 1900 + 1000


def get_crit_rate(crit: int) -> float:
    return 50 + (200 * (crit - 400) // 1900) / 1000


def get_dh_rate(dh: int) -> float:
    return (550 * (dh - 400) // 1900) / 1000


def get_crit_damage(crit: int) -> float:
    return (1000 + (200 * (crit - 400) // 1900 + 400)) / 1000


def get_gcd(sks: int) -> float:
    return (
        ((10000 * (2500 * (1000 - (130 * (sks - 400) // 1900)) // 1000) // 1000)) // 100
    ) / 100


def get_aa_damage(
    stats: DancerStats,
    crit_rate_bonus: float,
    dh_rate_bonus: float,
    damage_bonuses: list[float],
) -> DamageInfo:

    damage = f_ap(stats.dex) * 95 * f_wd(stats.wd) * (f_det(stats.det) // 1000) // 100

    for buff in damage_bonuses:
        damage = damage * buff // 1

    crit_damage = damage * (1000 * get_crit_damage(stats.crit)) // 1000
    dh_damage = damage * 1250 // 1000
    crit_dh_damage = crit_damage * 1250 // 1000
    crit_rate = get_crit_rate(stats.crit) + crit_rate_bonus
    dh_rate = get_dh_rate(stats.dh) + dh_rate_bonus

    return DamageInfo(
        hit=damage,
        crit_hit=crit_damage,
        dh_hit=dh_damage,
        crit_dh_hit=crit_dh_damage,
        crit_rate=crit_rate,
        dh_rate=dh_rate,
    )


def expected_value(info: DamageInfo) -> float:
    # This produces floats, wheras real damage is always an int. It might be better to generate a distribution instead in the future.
    # This isn't a method of DamageInfo due to knowing how this will and won't play nicely with acceleration tools I intend to add into this

    cdh_rate = info.crit_rate * info.dh_rate
    normal_rate = 1 - info.crit_rate - info.dh_rate + cdh_rate

    return (
        info.hit * normal_rate
        + info.crit_hit * (info.crit_rate - cdh_rate)
        + info.dh_hit * (info.dh_rate - cdh_rate)
        + info.crit_dh_hit * cdh_rate
    )


def calc_damage(
    potency: int,
    stats: DancerStats,
    crit_rate_bonus: float,
    dh_rate_bonus: float,
    damage_bonuses: list[float],
    auto_dh: bool = False,
    auto_crit: bool = False,
) -> DamageInfo:

    crit_damage_mod = get_crit_damage(stats.crit)

    auto_type_mods = 1
    if auto_crit:
        auto_type_mods *= (1 + crit_damage_mod * crit_rate_bonus)
    if auto_dh:
        auto_type_mods *= (1 + dh_rate_bonus * 0.25)


    trait_bonus = 1.3  # 1.3; trait bonuses @ 90, f_tnc step skipped for dnc

    damage = potency * f_ap(stats.dex) * f_det(stats.det) // 100
    damage = damage * auto_type_mods // 1

    # When I expand job support, this should become
    # damage = damage * f_tnc(stats.tnc) // 100 * f_wd(stats.wd) // 100 * trait_bonus // 1
    damage = damage * f_wd(stats.wd) // 100 * trait_bonus // 1


    for buff in damage_bonuses:
        damage = damage * buff // 1

    crit_damage = damage * (1000 * crit_damage_mod) // 1000
    dh_damage = damage * 1250 // 1000
    crit_dh_damage = crit_damage * 1250 // 1000
    crit_rate = 1 if auto_crit else get_crit_rate(stats.crit) + crit_rate_bonus
    dh_rate = 1 if auto_dh else get_dh_rate(stats.dh) + dh_rate_bonus

    return DamageInfo(
        hit=damage,
        crit_hit=crit_damage,
        dh_hit=dh_damage,
        crit_dh_hit=crit_dh_damage,
        crit_rate=crit_rate,
        dh_rate=dh_rate,
    )
