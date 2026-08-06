# Sekai2: From World Exploration to Interactive World Modeling

**Sekai2** is a large-scale, real-world egocentric video dataset built for interactive world models. It pairs long-horizon footage of people moving through the world — walking, driving, cycling, flying, riding rail, boats and cable cars — with camera trajectories and structured, temporally grounded language.

Kang He<sup>1,2,3</sup>, Wenshuo Peng<sup>4</sup>, Zihui Gao<sup>1</sup>, Jiaming Tan<sup>1</sup>, Kaipeng Zhang<sup>1,\*</sup>, Yongtao Ge<sup>1,\*</sup>

<sup>1</sup> Alaya Lab · <sup>2</sup> Shanghai Innovation Institute · <sup>3</sup> Wuhan University · <sup>4</sup> Tsinghua University
<sup>\*</sup> Corresponding authors

🌐 **[Project page](https://kangverse.github.io/sekai2-project/)** · 📄 Technical report — *coming soon* · 🤗 Dataset — *coming soon*

---

## The dataset at a glance

| | |
|---|---|
| Clips | **128,892** |
| Footage | **2,826 hours** |
| Countries and regions | **113** |
| Temporally grounded segments | **649,597** (5.04 per clip, 15 s median) |

Three sources, deliberately different in what they contribute:

| Source | Clips | Hours | Notes |
|---|---:|---:|---|
| Inherited Sekai | 47,699 | ~795 | every clip exactly 60 s |
| Newly collected YouTube | 80,211 | ~1,913 | mean 85.8 s, capped at 120 s |
| Panoramic (self-captured) | 982 | ~119 | 360°, released uncut, averaging 436 s |

Every clip ships with:

- **Camera pose** — per-frame trajectories from a geometry pipeline, validated against the images themselves
- **Clip-level annotation** — factorized description fields covering the scene, what moves, and how the camera behaves
- **Grounded segments** — each with its own time range, short prompt and camera path label
- **Controlled attributes** — country, camera motion, lighting, time of day, weather and scene type

## Code

**Coming soon.** The data pipeline, annotation tooling, and analysis code will be released here.

## Citation

The technical report is in preparation. A BibTeX entry will be added here on release.

## License

To be announced with the data release.
