from polars_styler.polars_styler import pydf_to_pystyler


class ColorMap:
    pass


class Styler:

    def __init__(self, s):
        self._s = s

    def set_precision(self, precision):
        self._s.set_precision(precision)
        return self

    def background_gradient(
        self,
        cmap: ColorMap = None,
        high: float = None,
        low: float = None,
        subset: list[str] = None,
        vmin: float = None,
        vmax: float = None,
        text_color_threshold: float = None,
    ):
        self._s.background_gradient(
            cmap=cmap,
            high=high,
            low=low,
            subset=subset,
            _vmin=vmin,
            _vmax=vmax,
            text_color_threshold=text_color_threshold,
        )
        return self

    def set_table_classes(self, classes: str | list[str]):
        if isinstance(classes, str):
            classes = [classes]
        self._s.set_table_classes(classes)
        return self

    def add_table_classes(self, classes: str | list[str]):
        if isinstance(classes, str):
            classes = [classes]
        self._s.add_table_classes(classes)
        return self

    def _prepare_ipynb_table(self):
        return self.add_table_classes("dataframe")

    def _repr_html_(self):
        return self._prepare_ipynb_table().render()

    def render(self):
        return self._s.render()


def style(df_self):
    # use this to patch pl.DataFrame.style

    py_styler = pydf_to_pystyler(df_self)
    return Styler(py_styler)
