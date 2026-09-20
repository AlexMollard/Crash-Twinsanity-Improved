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
  // `future.v4` turns on `mdx1CompatDisabledByDefault`, which switches off `mdx1Compat.admonitions`
  // - and that is what renders `:::note` in Docusaurus 3.x. Without this, every admonition on the
  // site came out as literal ":::note" text. `format` is pinned for the same reason: v4 changes the
  // default for .md files to CommonMark, which would not parse the directives either.
  markdown: {
    format: 'mdx',
    mdx1Compat: {admonitions: true},
    hooks: {onBrokenMarkdownLinks: 'warn'},
  },

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
