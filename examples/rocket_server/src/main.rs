#[macro_use]
extern crate rocket;

use polars::df;
use polars::prelude::*;
use polars_styler::colors::Color;
use polars_styler::styler::StylerExt;
use rocket::{Build, Rocket};
use rocket_dyn_templates::{context, Template};

#[get("/")]
fn index() -> Template {
    let data = df!(
        "Fruit" => &["Apple", "Apple", "Pear"],
        "Color" => &["Red", "Yellow", "Green"],
        "Price" => &[1.23, 2.34, 3.45],
    );
    let data = data.unwrap();
    let context = context! {
        data: data.style()
        .background_gradient("Price", &Color::new(230, 30, 40))
        .set_table_classes(vec![
            "table".to_string(),
            "table-hover".to_string(),
            "table-bordered".to_string(),
        ])
        .render(),
    };
    Template::render("index", &context)
}

#[launch]
fn rocket() -> Rocket<Build> {
    rocket::build()
        .mount("/", routes![index])
        .attach(Template::fairing())
}
