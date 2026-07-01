import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
import imageio.v2 as imageio
import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.util import add_cyclic_point

try:
    from geocat.comp.interpolation import interp_hybrid_to_pressure
except ImportError:
    interp_hybrid_to_pressure = None


# -------------------------------------------------------------------
# À MODIFIER
# -------------------------------------------------------------------
FILE_PATTERN = "atm/hist/*.cam.h0.*.nc"
OUTDIR = "frames_prect_u850"
GIF_NAME = "CESM_PRECT_U850_12months.gif"

# Échelle visuelle pluie
PRECIP_VMIN = 0
PRECIP_VMAX = 14  # mm/day ; monte à 20 si les tropiques saturent

# Nombre max de frames
NFRAMES = 12
# -------------------------------------------------------------------


def month_label(t):
    """Gère numpy datetime64 et cftime."""
    try:
        return pd.to_datetime(t).strftime("%b %Y")
    except Exception:
        if hasattr(t, "strftime"):
            return t.strftime("%b %Y")
        return str(t)[:10]


def get_p0(ds):
    if "P0" in ds:
        return float(ds["P0"].values)
    return 100000.0


def get_850_wind(ds):
    """
    Retourne U850, V850.
    Cas 1 : variables U850/V850 déjà présentes.
    Cas 2 : interpolation depuis U/V hybrides vers 850 hPa.
    """
    if "U850" in ds and "V850" in ds:
        return ds["U850"], ds["V850"]

    required = ["U", "V", "PS", "hyam", "hybm"]
    missing = [v for v in required if v not in ds]

    if missing:
        raise ValueError(
            f"Impossible de calculer U850/V850. Variables manquantes : {missing}\n"
            "Solution : refaire une sortie CAM avec U/V/PS/hyam/hybm, "
            "ou ajouter directement U850/V850."
        )

    if interp_hybrid_to_pressure is None:
        raise ImportError(
            "geocat-comp n'est pas installé. Utilisez :\n"
            "mamba install -c conda-forge geocat-comp"
        )

    new_lev = np.array([85000.0])  # 850 hPa en Pa
    p0 = get_p0(ds)

    u850 = interp_hybrid_to_pressure(
        ds["U"],
        ds["PS"],
        ds["hyam"],
        ds["hybm"],
        p0=p0,
        new_levels=new_lev,
        lev_dim="lev",
        method="linear",
        extrapolate=False,
    ).squeeze(drop=True)

    v850 = interp_hybrid_to_pressure(
        ds["V"],
        ds["PS"],
        ds["hyam"],
        ds["hybm"],
        p0=p0,
        new_levels=new_lev,
        lev_dim="lev",
        method="linear",
        extrapolate=False,
    ).squeeze(drop=True)

    return u850, v850


def main():
    files = sorted(glob.glob(FILE_PATTERN))
    if not files:
        raise FileNotFoundError(f"Aucun fichier trouvé avec : {FILE_PATTERN}")

    os.makedirs(OUTDIR, exist_ok=True)

    print(f"Ouverture de {len(files)} fichiers...")
    ds = xr.open_mfdataset(
        files,
        combine="by_coords",
        chunks={"time": 1},
        decode_times=True,
    )

    if "PRECT" not in ds:
        raise ValueError("Variable PRECT absente des fichiers.")

    # Conversion : m/s -> mm/day
    prect = ds["PRECT"] * 1000.0 * 86400.0
    prect.attrs["units"] = "mm/day"

    u850, v850 = get_850_wind(ds)

    lon = ds["lon"]
    lat = ds["lat"]

    ntime = min(NFRAMES, prect.sizes["time"])
    frame_files = []

    for it in range(ntime):
        print(f"Frame {it + 1}/{ntime}")

        rain = prect.isel(time=it).load()
        u = u850.isel(time=it).load()
        v = v850.isel(time=it).load()

        # Ajoute un point cyclique pour éviter une ligne blanche au méridien 0/360
        rain_cyc, lon_cyc = add_cyclic_point(rain.values, coord=lon.values)

        fig = plt.figure(figsize=(13, 7), dpi=170)
        proj = ccrs.Robinson()
        ax = plt.axes(projection=proj)
        ax.set_global()

        ax.add_feature(cfeature.LAND, facecolor="lightgray", alpha=0.35, zorder=0)
        ax.coastlines(linewidth=0.6)

        # im = ax.pcolormesh(
        #     lon_cyc,
        #     lat.values,
        #     rain_cyc,
        #     transform=ccrs.PlateCarree(),
        #     cmap="turbo",
        #     vmin=PRECIP_VMIN,
        #     vmax=PRECIP_VMAX,
        #     shading="auto",
        # )

        levels = np.arange(PRECIP_VMIN, PRECIP_VMAX + 0.5, 0.5)

        im = ax.contourf(
            lon_cyc,
            lat.values,
            rain_cyc,
            levels=levels,
            transform=ccrs.PlateCarree(),
            cmap="turbo",
            extend="max",
)


        # Vents 850 hPa : Cartopy peut rééchantillonner avec regrid_shape.
        q = ax.quiver(
            lon.values,
            lat.values,
            u.values,
            v.values,
            transform=ccrs.PlateCarree(),
            regrid_shape=28,
            scale=520,
            width=0.0022,
            alpha=0.9,
        )

        ax.quiverkey(
            q,
            X=0.88,
            Y=-0.08,
            U=10,
            label="10 m/s",
            labelpos="E",
        )

        tlabel = month_label(prect["time"].values[it])

        ax.set_title(
            f"CESM F2000clim — precipitation + 850 hPa winds\n{tlabel}",
            fontsize=15,
            pad=14,
        )

        cbar = plt.colorbar(
            im,
            ax=ax,
            orientation="horizontal",
            pad=0.055,
            fraction=0.045,
        )
        cbar.set_label("Total precipitation PRECT [mm/day]")

        fig.text(
            0.5,
            0.015,
            "12-month CESM atmosphere-land simulation — technical port validation",
            ha="center",
            fontsize=9,
        )

        frame_path = os.path.join(OUTDIR, f"frame_{it:02d}.png")
        fig.savefig(frame_path, bbox_inches="tight")
        plt.close(fig)

        frame_files.append(frame_path)

    print("Création du GIF...")
    frames = [imageio.imread(f) for f in frame_files]
    imageio.mimsave(GIF_NAME, frames, duration=750, loop=0)

    print(f"GIF écrit : {GIF_NAME}")


if __name__ == "__main__":
    main()