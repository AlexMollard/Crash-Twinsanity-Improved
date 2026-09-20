import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Crash Twinsanity Improved',
  tagline: 'How the game works, and how this mod changes it',
  favicon: 'img/favicon.svg',

  future: {v4: true},

  url: 'https://alexmollard.github.io',
  baseUrl: '/Crash-Twinsanity-Improved/',
  organizationName: 'AlexMollard',
  projectName: 'Crash-Twinsanity-Improved',
  trailingSlash: false,

  onBrokenLinks: 'throw',
  markdown: {hooks: {onBrokenMarkdownLinks: 'warn'}},

  i18n: {defaultLocale: 'en', locales: ['en']},

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          editUrl:
            'https://github.com/AlexMollard/Crash-Twinsanity-Improved/tree/main/wiki/',
        },
        blog: false,
        theme: {customCss: './src/css/custom.css'},
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {defaultMode: 'dark', respectPrefersColorScheme: true},
    navbar: {
      title: 'Twinsanity Improved',
      logo: {alt: 'Crash Twinsanity Improved', src: 'img/logo.svg'},
      items: [
        {type: 'docSidebar', sidebarId: 'wiki', position: 'left', label: 'Wiki'},
        {
          href: 'https://github.com/AlexMollard/Crash-Twinsanity-Improved',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'The engine',
          items: [
            {label: 'Scripts', to: '/engine/scripts'},
            {label: 'Cutscenes', to: '/engine/cutscenes'},
            {label: 'Objects and agents', to: '/engine/objects'},
          ],
        },
        {
          title: 'Modding',
          items: [
            {label: 'Building the ISO', to: '/modding/build'},
            {label: 'Level recipes', to: '/modding/recipes'},
            {label: 'Executable patches', to: '/modding/elf-patches'},
          ],
        },
        {
          title: 'Elsewhere',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/AlexMollard/Crash-Twinsanity-Improved',
            },
            {
              label: 'Twinsanity Editor',
              href: 'https://github.com/Smartkin/twinsanity-editor',
            },
            {
              label: 'twinsanity-reversed',
              href: 'https://github.com/Smartkin/twinsanity-reversed',
            },
          ],
        },
      ],
      copyright:
        'An unofficial fan project. Crash Twinsanity is © its respective owners.',
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'ini'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
