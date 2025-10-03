"""GraphQL queries for JustWatch API."""

# GraphQL query to search for content by title
SEARCH_QUERY = """
query GetSearchTitles(
    $searchTitlesFilter: TitleFilter!
    $country: Country!
    $language: Language!
    $first: Int! = 5
    $sortBy: PopularTitlesSorting! = POPULAR
) {
    popularTitles(
        country: $country
        filter: $searchTitlesFilter
        first: $first
        sortBy: $sortBy
    ) {
        edges {
            node {
                id
                objectType
                objectId
                content(country: $country, language: $language) {
                    title
                    originalReleaseYear
                    externalIds {
                        imdbId
                        tmdbId
                    }
                }
            }
        }
    }
}
"""

# GraphQL query to get streaming offers for content
OFFERS_QUERY = """
query GetTitleOffers(
    $nodeId: ID!
    $country: Country!
    $filterBuy: OfferFilter!
    $filterFlatrate: OfferFilter!
    $filterRent: OfferFilter!
    $filterFree: OfferFilter!
) {
    node(id: $nodeId) {
        id
        ... on MovieOrShowOrSeason {
            objectType
            objectId
            offerCount(country: $country, platform: WEB)
            offers(country: $country, platform: WEB) {
                monetizationType
                presentationType
                package {
                    id
                    packageId
                    clearName
                    shortName
                    technicalName
                }
            }
            flatrate: offers(
                country: $country
                platform: WEB
                filter: $filterFlatrate
            ) {
                monetizationType
                presentationType
                package {
                    id
                    packageId
                    clearName
                    shortName
                    technicalName
                }
            }
            buy: offers(country: $country, platform: WEB, filter: $filterBuy) {
                monetizationType
                presentationType
                package {
                    id
                    packageId
                    clearName
                    shortName
                    technicalName
                }
            }
            rent: offers(country: $country, platform: WEB, filter: $filterRent) {
                monetizationType
                presentationType
                package {
                    id
                    packageId
                    clearName
                    shortName
                    technicalName
                }
            }
            free: offers(country: $country, platform: WEB, filter: $filterFree) {
                monetizationType
                presentationType
                package {
                    id
                    packageId
                    clearName
                    shortName
                    technicalName
                }
            }
        }
    }
}
"""

# GraphQL query to get available providers for a locale
PROVIDERS_QUERY = """
query GetProviders($country: Country!) {
    packages(country: $country, platform: WEB) {
        id
        packageId
        clearName
        shortName
        technicalName
        monetizationTypes
    }
}
"""
