// Safe svgo config for the logo SVGs: keep viewBox and keep IDs
// (the arc <path id="topArc"/"botArc"> are referenced by <textPath href>).
export default {
  multipass: true,
  plugins: [
    {
      name: 'preset-default',
      params: {
        floatPrecision: 5,
        overrides: {
          cleanupIds: false,
          convertPathData: { floatPrecision: 5 },
          convertTransform: { floatPrecision: 5 },
          cleanupNumericValues: { floatPrecision: 5 },
        },
      },
    },
  ],
};
