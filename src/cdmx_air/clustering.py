"""K-Means / GMM model selection and cluster profiling."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture

from .config import RANDOM_STATE

PRIMARY_POLLUTANTS = ["CO", "NO", "NO2", "PM10", "PM25"]

SCENARIO_NAMES = {
    "clean": "Clean air",
    "moderate": "Moderate urban",
    "ozone": "Ozone peak",
    "high": "High pollution",
}
SCENARIO_ORDER = ["Clean air", "Moderate urban", "Ozone peak", "High pollution"]


def evaluate_k(
    X: np.ndarray,
    k_values: range = range(2, 9),
    silhouette_sample: int = 10_000,
) -> pd.DataFrame:
    """Inertia and silhouette for K-Means, BIC and silhouette for GMM, per k.

    Silhouette is O(n²), so it is estimated on a random sample of rows.
    """
    rows = []
    for k in k_values:
        km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE).fit(X)
        gmm = GaussianMixture(n_components=k, random_state=RANDOM_STATE).fit(X)
        rows.append(
            {
                "k": k,
                "kmeans_inertia": km.inertia_,
                "kmeans_silhouette": silhouette_score(
                    X, km.labels_, sample_size=silhouette_sample, random_state=RANDOM_STATE
                ),
                "gmm_bic": gmm.bic(X),
                "gmm_silhouette": silhouette_score(
                    X, gmm.predict(X), sample_size=silhouette_sample, random_state=RANDOM_STATE
                ),
            }
        )
    return pd.DataFrame(rows).set_index("k")


def fit_kmeans(X: np.ndarray, n_clusters: int, n_init: int = 20) -> KMeans:
    return KMeans(n_clusters=n_clusters, n_init=n_init, random_state=RANDOM_STATE).fit(X)


def cluster_profile(X: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """Mean of each (scaled) feature per cluster, plus the cluster's share of rows."""
    profile = X.groupby(labels).mean()
    profile["share_pct"] = pd.Series(labels).value_counts(normalize=True).sort_index() * 100
    return profile.round(2)


def name_scenarios(centroids: pd.DataFrame) -> dict[int, str]:
    """Map the 4 K-Means centroids (in standardized units) to scenario names.

    K-Means label numbers are arbitrary, so names are assigned from the
    centroids instead of hard-coding "cluster 2 = clean air":
      * Ozone peak: highest O3.
      * High pollution: highest mean of the primary (combustion) pollutants.
      * Clean air: lowest mean over all features.
      * Moderate urban: the remaining cluster.
    """
    if len(centroids) != 4:
        raise ValueError("Scenario naming is defined for k = 4.")
    remaining = list(centroids.index)
    names = {}

    ozone = centroids.loc[remaining, "O3"].idxmax()
    names[ozone] = SCENARIO_NAMES["ozone"]
    remaining.remove(ozone)

    high = centroids.loc[remaining, PRIMARY_POLLUTANTS].mean(axis=1).idxmax()
    names[high] = SCENARIO_NAMES["high"]
    remaining.remove(high)

    clean = centroids.loc[remaining].mean(axis=1).idxmin()
    names[clean] = SCENARIO_NAMES["clean"]
    remaining.remove(clean)

    names[remaining[0]] = SCENARIO_NAMES["moderate"]
    return names


def transition_matrix(df: pd.DataFrame, column: str = "scenario") -> pd.DataFrame:
    """Probability (%) of moving from one scenario to another in the next hour.

    Transitions are computed within each station's own hourly series.
    """
    df = df.sort_values(["station", "datetime"])
    next_state = df.groupby("station")[column].shift(-1)
    valid = next_state.notna()
    return pd.crosstab(df.loc[valid, column], next_state[valid], normalize="index") * 100
