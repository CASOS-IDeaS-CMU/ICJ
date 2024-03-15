# fonts.py
# Daniele Bellutta
# 20 May 2021


DEFAULT_FAMILY = "serif"
DEFAULT_FONT = "Times New Roman"


def set_font(plt, family, font):
  plt.rcParams["font.family"] = str(family)
  plt.rcParams["font.%s" % (str(family))] = [str(font)]
  plt.rcParams["mathtext.fontset"] = "custom"
  plt.rcParams["mathtext.rm"] = str(font)
  plt.rcParams["mathtext.it"] = ("%s:italic" % (str(font)))
  plt.rcParams["mathtext.bf"] = ("%s:bold" % (str(font)))


