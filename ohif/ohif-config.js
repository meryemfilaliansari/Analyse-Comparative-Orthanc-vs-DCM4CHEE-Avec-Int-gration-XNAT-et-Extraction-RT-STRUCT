window.config = {
  routerBasename: '/',
  extensions: [],
  modes: [],
  showStudyList: true,
  dataSources: [
    {
      namespace: '@ohif/extension-default.dataSourcesModule.dicomweb',
      sourceName: 'orthanc-user',
      configuration: {
        friendlyName: 'Orthanc Student - Données Anonymisées',
        name: 'orthanc-user',
        wadoUriRoot: 'http://localhost:8043/wado',
        qidoRoot: 'http://localhost:8043/dicom-web',
        wadoRoot: 'http://localhost:8043/dicom-web',
        qidoSupportsIncludeField: false,
        imageRendering: 'wadors',
        thumbnailRendering: 'wadors',
        enableStudyLazyLoad: true,
        supportsFuzzyMatching: false,
        supportsWildcard: true,
        staticWado: true,
        singlepart: 'bulkdata,video',
        bulkDataURI: {
          enabled: true,
          relativeResolution: 'studies',
        },
      },
    },
  ],
  defaultDataSourceName: 'orthanc-user',
};
