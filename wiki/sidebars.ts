import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  wiki: [
    'intro',
    {
      type: 'category',
      label: 'The engine',
      collapsed: false,
      items: [
        'engine/overview',
        'engine/scripts',
        'engine/cutscenes',
        'engine/objects',
        'engine/archive',
        'engine/executable',
        'engine/loading',
        'engine/movies',
        'engine/graphics',
        'engine/lighting',
      ],
    },
    {
      type: 'category',
      label: 'Modding',
      collapsed: false,
      items: [
        'modding/build',
        'modding/recipes',
        'modding/elf-patches',
        'modding/rig',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      collapsed: false,
      items: ['reference/script-ids', 'reference/addresses', 'reference/glossary'],
    },
  ],
};

export default sidebars;
