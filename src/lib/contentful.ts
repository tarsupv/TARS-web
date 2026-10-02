import contentful, {
  type ContentfulClientApi,
  type Entry,
  type EntryFieldTypes,
} from "contentful";

export interface work {
  contentTypeId: "blogTars";
  fields: {
    title: EntryFieldTypes.Text;
    slug: EntryFieldTypes.Text;
    date: EntryFieldTypes.Date;
    headerImg: EntryFieldTypes.AssetLink;
    description: EntryFieldTypes.Text;
    content: EntryFieldTypes.RichText;
    category: EntryFieldTypes.Text;
    readTime: EntryFieldTypes.Number;
    author: EntryFieldTypes.Text;
    authorImage: EntryFieldTypes.AssetLink;
    tags: EntryFieldTypes.Symbol[];
  };
}

const space = import.meta.env.CONTENTFUL_SPACE_ID;
const accessToken = import.meta.env.DEV
  ? import.meta.env.CONTENTFUL_PREVIEW_TOKEN
  : import.meta.env.CONTENTFUL_DELIVERY_TOKEN;

export const contentfulConfigured = Boolean(space && accessToken);

// createClient lanza al importarse si faltan credenciales, y eso tumbaba la home
// entera en local. Sin credenciales se exporta un cliente que solo falla al
// usarse, con un mensaje que dice que falta.
export const contentfulClient: ContentfulClientApi<undefined> = contentfulConfigured
  ? contentful.createClient({
      space,
      accessToken,
      host: import.meta.env.DEV ? "preview.contentful.com" : "cdn.contentful.com",
    })
  : (new Proxy({}, {
      get() {
        throw new Error(
          "Contentful no configurado: faltan CONTENTFUL_SPACE_ID y el token en .env"
        );
      },
    }) as ContentfulClientApi<undefined>);

/**
 * Ultimos posts del blog. En desarrollo, si Contentful no esta configurado o no
 * responde, devuelve [] para poder trabajar el resto de la pagina; en produccion
 * el error se propaga y el build falla, en vez de publicar una home sin noticias.
 */
export async function getLatestPosts(limit?: number) {
  try {
    const entries = await contentfulClient.getEntries<work>({
      content_type: "blogTars",
      order: ["-fields.date"],
      ...(limit ? { limit } : {}),
    });
    return entries.items;
  } catch (error) {
    if (!import.meta.env.DEV) throw error;
    console.warn(`[contentful] sin noticias en local: ${(error as Error).message}`);
    return [];
  }
}
