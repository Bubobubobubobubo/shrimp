import { after } from "node:test"
import { ExtendedPageLayout, PageLayout, SharedLayout } from "./quartz/cfg"
import * as Component from "./quartz/components"

// components shared across all pages
export const sharedPageComponents: SharedLayout = {
  head: Component.Head(),
  header: [],
  afterBody: [],
  footer: Component.Footer({
    links: {
      GitHub: "https://github.com/jackyzha0/quartz",
      "Discord Community": "https://discord.gg/cRFFHYye7t",
    },
  }),
}


const ExplorerConfig = {
  title: "Sections",
  useSavedState: true,
  order: ["sort", "map", "filter",],
}

const graphConfig = {
    localGraph: {
      scale: 1.5,
      depth: 5,
      linkDistance: 30,
      opacityScale: 1.25,
    },
    globalGraph: {} 
}

// components for pages that display a single page (e.g. a single note)
export const defaultContentPageLayout: ExtendedPageLayout = {
  beforeBody: [
    Component.ArticleTitle(),
    // Component.ContentMeta(),
  ],
  afterBody: [
    Component.TagList(),
    Component.Graph(graphConfig),
  ],
  left: [
    Component.MobileOnly(Component.Spacer()),
    Component.Search(),
    Component.DesktopOnly(Component.Explorer(ExplorerConfig)),
  ],
  right: [
    Component.PageTitle(),
    Component.Darkmode(),
    Component.Graph(),
    Component.DesktopOnly(Component.TableOfContents()),
    Component.Backlinks(),
  ],
}

// components for pages that display lists of pages (e.g. tags or folders)
export const defaultListPageLayout: PageLayout = {
  beforeBody: [
    Component.ArticleTitle(), 
    //Component.ContentMeta()
  ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Search(),
    Component.Darkmode(),
    Component.DesktopOnly(Component.Explorer(ExplorerConfig)),
  ],
  afterBody: [
  ],
  right: [
    Component.Graph({
      localGraph: {
        depth: 5,
      },
      globalGraph: {},
    }),
  ],
}
