export const SERVICE_CARDS = [
  {
    slug: "tarmac-restoration",
    name: "Tarmac restoration",
    blurb: "Wash, prepare and coat tired tarmac so a sound driveway can be restored instead of replaced.",
    href: "/services/tarmac-restoration",
    estimate: "instant",
  },
  {
    slug: "block-paving",
    name: "Block paving restoration",
    blurb: "Clean, re-sand and seal block paving where the blocks and base are suitable to keep.",
    href: "/services/block-paving",
    estimate: "on-request",
  },
  {
    slug: "imprinted-concrete",
    name: "Pattern-imprinted concrete restoration",
    blurb: "Bring back colour and protection on pattern-imprinted concrete after the right preparation.",
    href: "/services/imprinted-concrete",
    estimate: "on-request",
  },
  {
    slug: "minor-repairs",
    name: "Surface repairs",
    blurb: "Local repairs that may be needed alongside restoration. Agreed and priced before they are added.",
    href: "/services/minor-repairs",
    estimate: "on-request",
  },
  {
    slug: "commercial-restoration",
    name: "Commercial surface restoration",
    blurb: "Restoration for forecourts, yards and business hardstanding, quoted for the site in front of us.",
    href: "/services/commercial-restoration",
    estimate: "on-request",
  },
  {
    slug: "commercial-car-parks",
    name: "Car park restoration and line marking",
    blurb: "Car park surfaces and line marking, scoped to the site. No published price until one is confirmed.",
    href: "/services/commercial-car-parks",
    estimate: "on-request",
  },
] as const;

export type ServiceEstimate = (typeof SERVICE_CARDS)[number]["estimate"];

export const WHY_RESTORE = [
  "Potentially lower cost than replacement.",
  "Less disruption.",
  "Improved kerb appeal.",
  "Professional surface preparation.",
  "Restoration of faded colour.",
  "Suitable protective coatings.",
] as const;

export const HOW_IT_WORKS = [
  {
    title: "Get your instant estimate.",
    detail: "Enter the property, the surface and the measurements. Photographs are optional and do not hold up the price.",
  },
  {
    title: "Request your booking.",
    detail: "Ask us to book you in, call you back, or email the estimate. A request is not a confirmed appointment.",
  },
  {
    title: "We professionally clean and prepare your driveway.",
    detail: "Where washing is part of the work, that visit comes first so the surface is ready to coat.",
  },
  {
    title: "We return to apply the specialist restoration coating.",
    detail: "The coating visit is arranged after preparation. It goes ahead when the weather and the surface are suitable.",
  },
] as const;

export const FAQ_ITEMS = [
  {
    q: "How much does restoration cost?",
    a: "Tarmac restoration has a published instant estimate. You enter the measurements and see one total. Travel and preparation are included in that total where they apply, and are not listed as separate charges. Block paving, pattern-imprinted concrete, repairs and commercial work are priced only when a rate has been set. We will not guess a figure. A photograph does not add a repair charge on its own. Any repair is agreed with you before it is included. SurfaceCoat is not VAT registered, so the estimate is not shown with VAT added.",
  },
  {
    q: "How long does the process take?",
    a: "Where the driveway is washed and then coated, that is two visits. The coating visit follows once the surface has had time to dry. We do not publish a single duration for every driveway, because it depends on the area and the conditions on the day.",
  },
  {
    q: "Can you repair cracks and damaged areas?",
    a: "Minor wear around edges is normal and is not an automatic extra. If you have cracks or areas that may need repairing, add a close-up photograph. Significant defects are reviewed and priced separately, and they are included only after you agree. A photograph cannot confirm the structure of the driveway.",
  },
  {
    q: "Do I need to be at home?",
    a: "You do not need to be at home to receive an estimate. On the day we need safe access to the surface. If you cannot be there, arrange that access before the visit. We will tell you anything else required when the visit is agreed.",
  },
  {
    q: "What happens if it rains?",
    a: "Coating appointments depend on suitable weather and surface conditions. If rain or a damp surface would spoil the finish, we move the coating visit rather than apply a coating that cannot cure properly.",
  },
  {
    q: "When can I drive on my driveway again?",
    a: "We confirm the return-to-use time for the coating used on your driveway before we leave. Do not drive on the surface until that time has passed. It depends on the product and the conditions, so it is not the same number for every job.",
  },
  {
    q: "What surfaces can you restore?",
    a: "Tarmac, block paving and pattern-imprinted concrete, together with surface repairs where the driveway is suitable. Commercial surfaces, car parks and line marking are quoted for the site. An instant price is available for tarmac restoration. We will say when a surface is not suitable for restoration.",
  },
] as const;

export const PRIORITY_TOWNS = [
  "Blackpool",
  "Liverpool",
  "Manchester",
  "Preston",
  "Southport",
  "Ormskirk",
  "Burscough",
  "Formby",
  "Bolton",
  "Wigan",
  "Burnley",
  "Warrington",
  "Chorley",
  "Accrington",
  "Blackburn",
] as const;

export const LOCAL_PAGES = [
  {
    slug: "tarmac-restoration-blackpool",
    label: "Tarmac restoration in Blackpool",
    title: "Tarmac restoration in Blackpool and the Fylde Coast",
    intro:
      "Coastal weather fades tarmac. Where the driveway is sound, we clean and prepare it, then return to apply a restoration coating when conditions allow.",
    bullets: [
      "Blackpool, Lytham, St Annes, Fleetwood and Thornton-Cleveleys are within the area we cover.",
      "An instant tarmac estimate uses your measurements and shows one total.",
      "Washing and coating are separate visits when both are required.",
    ],
  },
  {
    slug: "driveway-restoration-liverpool",
    label: "Driveway restoration in Liverpool",
    title: "Driveway restoration in Liverpool and Merseyside",
    intro:
      "We restore suitable tarmac, and we describe block paving and pattern-imprinted concrete on their own pages. An instant price is published for tarmac restoration.",
    bullets: [
      "Liverpool, and suitable work towards Wirral, Knowsley and St Helens.",
      "Irregular driveways can be entered as separate measured sections.",
      "Coating visits are planned around drying time and the weather.",
    ],
  },
  {
    slug: "tarmac-restoration-manchester",
    label: "Tarmac restoration in Manchester",
    title: "Tarmac restoration in Greater Manchester",
    intro:
      "Greater Manchester driveways take heavy use and regular rain. We restore suitable tarmac after preparation, and we move a coating visit if the surface is not ready.",
    bullets: [
      "Bolton, Bury, Salford, Trafford, Stockport and surrounding districts we can reach.",
      "The online estimate is one total for the tarmac work described.",
      "Car parks and commercial yards are quoted on their own pages, without a guessed price.",
    ],
  },
  {
    slug: "driveway-restoration-southport",
    label: "Driveway restoration in Southport",
    title: "Driveway restoration in Southport and Sefton",
    intro:
      "Where the base is sound, restoration can refresh a faded driveway without digging it out. Moss, algae and surface wear are looked at before any coating is agreed.",
    bullets: [
      "Southport, Formby, Crosby, Maghull and Ainsdale.",
      "You can request an estimate at any time. A request is not a confirmed visit.",
      "We tell you if the surface needs a different approach.",
    ],
  },
  {
    slug: "tarmac-restoration-preston",
    label: "Tarmac restoration in Preston",
    title: "Tarmac restoration in Preston and Central Lancashire",
    intro:
      "We restore suitable tarmac in Preston, Leyland, Penwortham and the surrounding towns. Preston is part of the area we cover. We do not publish a premises address.",
    bullets: [
      "Preston, Leyland, Penwortham, Longton and Garstang.",
      "The instant tarmac estimate is one customer total.",
      "Repairs are priced only after they are agreed. They are not added from a photograph alone.",
    ],
  },
] as const;
